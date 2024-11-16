from datetime import datetime

from pydantic import BaseModel


class QuizSchema(BaseModel):
    id: int
    title: str
    description: str
    image: str | None
    created_at: datetime
    questions_count: int
    total_submissions_count: int
    successful_submissions_count: int
    avg_time_spent_sec: float


class QuizQuestionSchema(BaseModel):
    id: int
    title: str
    description: str
    image: str | None
    created_at: datetime
    total_answers: int
    correct_answers: int
    avg_time_spent_sec: float


class QuizDetailSchema(QuizSchema):
    questions: list[QuizQuestionSchema]


class QuizStats(BaseModel):
    quizzes_count: int
    submissions_count: int
    successful_submissions_count: int
    avg_time_spent_sec: float
