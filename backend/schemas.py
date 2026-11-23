from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    bio: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class PostCreate(BaseModel):
    author_id: str
    text: str
    tags: list[str] = []


class CommentCreate(BaseModel):
    user_id: str
    text: str