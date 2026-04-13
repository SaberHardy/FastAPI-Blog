from pydantic import BaseModel, ConfigDict, Field


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
