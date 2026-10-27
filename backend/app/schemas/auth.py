from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    assigned_attraction_id: str | None = None
    assigned_attraction_name: str | None = None


class SessionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
