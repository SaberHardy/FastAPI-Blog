from pydantic import BaseModel, ConfigDict, Field, EmailStr


class UserBase(BaseModel):
    """
    This class will have what's shared between UserCreate and UserResponse
    """
    username: str = Field(min_length=1, max_length=50)
    email: str = EmailStr  # we don't need to add the min length here bcz pydantic already does that
    password: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)  # this will pydantic to read data from sqlalchemy model
    id: int
    image_file: str | None
    image_path: str


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    """
    This class will inherit all the fields from PostBase, and we can add additional fields that are relevant for the response.
    """
    # What you will return to the user from the API
    # this will pydantic to read data from Objects instead of dicts, if from_attributes=True
    # so you can return an ORM object and it will read the data from it
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: str
