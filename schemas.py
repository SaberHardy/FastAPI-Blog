from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    """
    This class will have what's shared between UserCreate and UserResponse
    """
    username: str = Field(min_length=1, max_length=50)
    email: str = EmailStr  # we don't need to add the min length here bcz pydantic already does that
    # password: str = Field(min_length=1, max_length=50)
    # first_name: str = Field(min_length=1, max_length=50)
    # last_name: str = Field(min_length=1, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # this will pydantic to read data from sqlalchemy model
    id: int
    username: str
    image_file: str | None
    image_path: str


class UserPrivate(UserPublic):
    email: EmailStr


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    image_file: str | None = Field(default=None, min_length=1, max_length=200)


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    # this is removed because will come from the relationship
    # author: str = Field(min_length=1, max_length=50)


class PostCreate(PostBase):
    # user_id: int
    pass



class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)


class PostResponse(PostBase):
    """
    This class will inherit all the fields from PostBase, and we can add additional fields that are relevant for the response.
    """
    # What you will return to the user from the API
    # this will pydantic to read data from Objects instead of dicts, if from_attributes=True
    # so you can return an ORM object and it will read the data from it
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: datetime
    author: UserPublic
