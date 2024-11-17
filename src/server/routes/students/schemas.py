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
