from pydantic import BaseModel


class QuizStats(BaseModel):
    quizzes_count: int
    submissions_count: int
    successful_submissions_count: int
    avg_time_spent_sec: float
