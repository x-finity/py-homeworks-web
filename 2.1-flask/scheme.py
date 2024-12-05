from pydantic import BaseModel, field_validator


class BaseUser(BaseModel):
    password: str
    @field_validator("password")
    @classmethod
    def check_password(cls, value: str):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

class CreateUser(BaseUser):
    name: str
    password: str

class UpdateUser(BaseUser):
    name: str | None = None
    password: str | None = None

class BaseAdvertisement(BaseModel):
    title: str
    description: str

class CreateAdvertisement(BaseAdvertisement):
    pass

class UpdateAdvertisement(BaseModel):
    title: str | None = None
    description: str | None = None