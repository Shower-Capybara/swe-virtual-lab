from pydantic import BaseModel


class TopStudent(BaseModel):
    id: int
    username: str
    name: str
    successful_submissions: int
    total_submissions: int


class StudentStats(BaseModel):
    total_students: int
    top_students: list[TopStudent]


class StudentQuiz(BaseModel):
    id: int
    title: str
    successful_submissions_count: int
    total_submissions_count: int
    avg_spent_time_seconds: int


class StudentSchema(BaseModel):
    username: str
    name: str
    successful_submissions: int
    total_submissions: int
    total_time_spent_sec: int


class StudentDetailSchema(StudentSchema):
    quizes: list[StudentQuiz]
