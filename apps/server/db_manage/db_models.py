from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    password: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    quiz_submissions: Mapped[List["QuizSubmission"]] = relationship(back_populates="user")
    challenge_submissions: Mapped[List["ChallengeSubmission"]] = relationship(back_populates="user")
    page_views: Mapped[List["PageView"]] = relationship(back_populates="user")

class Quiz(Base):
    __tablename__ = "quizes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text)
    image: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    questions: Mapped[List["QuizQuestion"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")
    submissions: Mapped[List["QuizSubmission"]] = relationship(back_populates="quiz")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizes.id"))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text)
    image: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    options: Mapped[List["QuizQuestionOption"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    answers: Mapped[List["QuizSubmissionAnswer"]] = relationship(back_populates="question")

class QuizQuestionOption(Base):
    __tablename__ = "quiz_question_options"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id"))
    text: Mapped[Optional[str]] = mapped_column(Text)
    image: Mapped[Optional[str]] = mapped_column(String(256))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    
    # Relationships
    question: Mapped["QuizQuestion"] = relationship(back_populates="options")
    answers: Mapped[List["QuizSubmissionAnswer"]] = relationship(back_populates="selected_option")

class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizes.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="quiz_submissions")
    quiz: Mapped["Quiz"] = relationship(back_populates="submissions")
    answers: Mapped[List["QuizSubmissionAnswer"]] = relationship(back_populates="submission", cascade="all, delete-orphan")

class QuizSubmissionAnswer(Base):
    __tablename__ = "quiz_submission_answer"
    
    submission_id: Mapped[int] = mapped_column(ForeignKey("quiz_submissions.id"), primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id"), primary_key=True)
    selected_option_id: Mapped[int] = mapped_column(ForeignKey("quiz_question_options.id"), primary_key=True)
    spent_time_seconds: Mapped[int]
    
    # Relationships
    submission: Mapped["QuizSubmission"] = relationship(back_populates="answers")
    question: Mapped["QuizQuestion"] = relationship(back_populates="answers")
    selected_option: Mapped["QuizQuestionOption"] = relationship(back_populates="answers")

class Challenge(Base):
    __tablename__ = "challenges"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text)
    image: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    submissions: Mapped[List["ChallengeSubmission"]] = relationship(back_populates="challenge")

class ChallengeSubmission(Base):
    __tablename__ = "challenge_submissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"))
    text: Mapped[str] = mapped_column(Text)
    execution_time_ms: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="challenge_submissions")
    challenge: Mapped["Challenge"] = relationship(back_populates="submissions")

class PageView(Base):
    __tablename__ = "page_views"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    url: Mapped[str] = mapped_column(String(256))
    duration: Mapped[Optional[int]]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="page_views")