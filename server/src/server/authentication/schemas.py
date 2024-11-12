from pydantic import BaseModel


class AutheticatedUser(BaseModel):
    username: str
