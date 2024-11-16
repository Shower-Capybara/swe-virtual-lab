import asyncio
import hashlib
import logging
import random
from datetime import datetime, timedelta
from typing import List, Tuple

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from server.db import async_session_maker, engine
from server.db.models import (
    Base,
    PageView,
    Quiz,
    QuizQuestion,
    QuizQuestionOption,
    QuizSubmission,
    QuizSubmissionAnswer,
    User,
)
from server.schemas import UserRole

logger = logging.getLogger(__name__)
fake = Faker()

QUESTIONS_PER_QUIZ = 10
OPTIONS_PER_QUESTION = 4


async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


class DataConsistencyManager:
    """Helper class to manage consistent timestamps and relationships"""

    @staticmethod
    def generate_sequential_dates(
        num_dates: int, start_date: datetime, max_interval_days: int = 7
    ) -> List[datetime]:
        """Generate a list of sequential dates with random intervals"""
        dates = []
        current_date = start_date
        for _ in range(num_dates):
            dates.append(current_date)
            # Add 1-7 days random interval
            days_to_add = random.randint(1, max_interval_days)
            current_date += timedelta(days=days_to_add)
        return dates

    @staticmethod
    def get_activity_window(
        user_created_at: datetime, entity_created_at: datetime
    ) -> Tuple[datetime, datetime]:
        """Get valid time window for user activity based on user and entity creation dates"""
        start_date = max(user_created_at, entity_created_at)
        end_date = datetime.utcnow()
        return start_date, end_date


class AsyncDatabaseSeeder:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.consistency_manager = DataConsistencyManager()

    @staticmethod
    def generate_password() -> str:
        """Generate a hashed password."""
        password = fake.password()
        return hashlib.sha256(password.encode()).hexdigest()

    async def seed_users(self, num_users: int, role: UserRole) -> List[User]:
        """Seed users table"""

        user_dates = self.consistency_manager.generate_sequential_dates(
            num_users,
            start_date=datetime.utcnow() - timedelta(days=365),  # Start from 1 year ago
            max_interval_days=7,
        )

        users = [
            User(
                name=fake.name(),
                password=self.generate_password(),
                role=role.value,
                created_at=created_at,
            )
            for created_at in user_dates
        ]

        self.session.add_all(users)
        await self.session.commit()
        logger.info(f"Seeded {num_users} users")
        return users

    async def seed_quizzes(self, num_quizzes: int) -> List[Quiz]:
        """Seed quizzes and related tables"""
        quiz_dates = self.consistency_manager.generate_sequential_dates(
            num_quizzes,
            start_date=datetime.utcnow()
            - timedelta(days=180),  # Start from 6 months ago
            max_interval_days=5,
        )

        quizzes = []
        for i, quiz_created_at in enumerate(quiz_dates):
            quiz = Quiz(
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=200),
                image=f"/images/quiz_{i}.jpg" if random.random() > 0.5 else None,
                created_at=quiz_created_at,
            )

            # Create questions for this quiz - same creation date as quiz
            for j in range(QUESTIONS_PER_QUIZ):
                question = QuizQuestion(
                    title=fake.sentence(),
                    description=fake.text(max_nb_chars=100),
                    image=f"/images/quiz_{i}_question_{j}.jpg"
                    if random.random() > 0.7
                    else None,
                    created_at=quiz_created_at,  # Same as quiz creation date
                )

                # Create options for this question - same creation date as question
                correct_option = random.randint(0, OPTIONS_PER_QUESTION - 1)
                for k in range(OPTIONS_PER_QUESTION):
                    option = QuizQuestionOption(
                        text=f"Option {k + 1}: {fake.sentence()}",
                        is_correct=(k == correct_option),
                    )
                    question.options.append(option)

                quiz.questions.append(question)

            quizzes.append(quiz)

        self.session.add_all(quizzes)
        await self.session.commit()
        logger.info(f"Seeded {num_quizzes} quizzes with consistent timestamps")
        return quizzes

    async def seed_submissions(self, users: List[User], quizzes: List[Quiz]):
        """Seed quiz submissions"""
        for user in users[:10]:  # First 10 users submit quizzes
            for quiz in quizzes[:5]:  # First 5 quizzes
                # Submission must be after both user and quiz creation
                start_date, end_date = self.consistency_manager.get_activity_window(
                    user.created_at, quiz.created_at
                )

                if start_date >= end_date:
                    continue  # Skip if user was created after quiz

                submission_date = fake.date_time_between(
                    start_date=start_date, end_date=end_date
                )

                submission = QuizSubmission(
                    user=user, quiz=quiz, created_at=submission_date
                )

                # Add answers for each question
                total_time = 0
                for question in quiz.questions:
                    # Spent time should sum up to a reasonable total (e.g., 5-15 min per quiz)
                    remaining_questions = len(quiz.questions) - len(submission.answers)
                    max_time = min(
                        300, (900 - total_time) // max(1, remaining_questions)
                    )
                    spent_time = random.randint(10, max_time)
                    total_time += spent_time

                    answer = QuizSubmissionAnswer(
                        question=question,
                        selected_option=random.choice(question.options),
                        spent_time_seconds=spent_time,
                    )
                    submission.answers.append(answer)

                self.session.add(submission)

        await self.session.commit()
        logger.info("Seeded quiz submissions with consistent timestamps")

    async def seed_page_views(self, users: List[User]):
        """Seed page views"""
        page_views = []

        for user in users:
            # Generate 5-20 page views per user
            num_views = random.randint(5, 20)

            # Page views should be after user creation
            view_dates = self.consistency_manager.generate_sequential_dates(
                num_views, start_date=user.created_at, max_interval_days=2
            )

            for view_date in view_dates:
                page_view = PageView(
                    user=user,
                    url=f"/{random.choice(['quiz', 'challenge', 'profile'])}/{random.randint(1, 100)}",
                    duration=random.randint(10, 300),  # 10-300 seconds
                    created_at=view_date,
                )
                page_views.append(page_view)

        self.session.add_all(page_views)
        await self.session.commit()
        logger.info("Seeded page views")


async def seed_database():
    """Main seeding function"""
    try:
        # Create tables
        await create_tables()

        # Create seeder instance
        async with async_session_maker() as session:
            seeder = AsyncDatabaseSeeder(session)

            # Seed data
            users = await seeder.seed_users(10, UserRole.STUDENT)
            quizzes = await seeder.seed_quizzes(5)
            await seeder.seed_submissions(users, quizzes)
            await seeder.seed_page_views(users)

        logger.info("Database seeded successfully")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())
