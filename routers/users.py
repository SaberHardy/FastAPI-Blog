from datetime import timedelta
from typing import Annotated

from PIL import UnidentifiedImageError
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from starlette.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

import models
from auth import CurrentUser, create_access_token, hash_password, verify_password
from config import settings
from database import get_db
from image_utils import process_profile_image, ImageExtensions, delete_profile_image
from schemas import (PostResponse, TokenSchema, UserCreate, UserPrivate,
                     UserPublic, UserUpdate)

router = APIRouter()


# @app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.username) == user.username.lower()))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    result = await db.execute(select(models.User).where(func.lower(models.User.email) == user.email.lower()))
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = models.User(username=user.username,
                           email=user.email.lower(),
                           password_hash=hash_password(user.password))

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/token", response_model=TokenSchema)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == form_data.username.lower()))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect Email or password",
                            headers={"WWW-Authenticated": "Bearer"})

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return TokenSchema(access_token=access_token, token_type="bearer")


# The frontend needs to know who logged in
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    """Get the currently authenticated user."""
    # user_id = verify_access_token(token)
    #
    # if user_id is None:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    #                         detail="Invalid or expired token",
    #                         headers={"WWW-Authenticate": "Bearer"})
    #
    # # Validate user_id is a valid integer (defense against malformed JWT)
    # try:
    #     user_id_int = int(user_id)
    # except (TypeError, ValueError):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    #                         detail="Invalid or expired token",
    #                         headers={"WWW-Authenticate": "Bearer"})
    #
    # result = await db.execute(select(models.User).where(models.User.id == user_id_int))
    # user = result.scalars().first()
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    #                         detail="User not found",
    #                         headers={"WWW-Authenticate": "Bearer"})
    # return user

    return current_user


@router.get("/{user_id}", response_model=UserPublic)  # , status_code=status.HTTP_201_CREATED)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.post("/{user_id}", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User Not Found")

    result = await db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()

    return posts


@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(user_id: int,
                      user_update: UserUpdate,
                      current_user: CurrentUser,
                      db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        # Why 403 instead of 401 ?
        # 403: user is authenticated, but, you don't have permission to update the post
        # 401: un-authorized user - invalid token for the current user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to update this user!")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.username is not None and user_update.username.lower() != user.username.lower():
        result = await db.execute(select(models.User)
                                  .where(func.lower(models.User.username) == user_update.username.lower()))
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User name already exists")

    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        result = await db.execute(select(models.User).where(func.lower(models.User.email) == user_update.email.lower()))
        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User name already exists")

    # After the validation, i can update only the fields are provided
    if user_update.username is not None:
        user.user_name = user_update.username.lower()

    if user_update.email is not None:
        user.email = user_update.email.lower()

    # if user_update.image_file is not None:
    #     user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int,
                      current_user: CurrentUser,
                      db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        # Why 403 instead of 401 ?
        # 403: user is authenticated, but, you don't have permission to update the post
        # 401: un-authorized user - invalid token for the current user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to delete this post")
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User Not Found")

    old_filename = user.image_file

    # We need to wait the data save first, and then we can delete the image profile
    await db.delete(user)
    await db.commit()

    if old_filename:
        delete_profile_image(old_filename)


@router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(user_id: int, file: UploadFile,
                                 current_user: CurrentUser,
                                 db: Annotated[AsyncSession, Depends(get_db)]):
    if current_user.id != user_id:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authorized to update this user's picture")

    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File too large to process."
                                   f"Maximum Size is {settings.max_upload_size_bytes // (1024 * 1024)}MB")

    try:
        new_filename = await run_in_threadpool(process_profile_image, content)
    except UnidentifiedImageError as err:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=f"Invalid image file. Please upload a valid image {ImageExtensions.to_list}") from err

    old_filename = current_user.image_file
    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_image(old_filename)

    return current_user


@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(user_id: int, file: UploadFile,
                                 current_user: CurrentUser,
                                 db: Annotated[AsyncSession, Depends(get_db)]):
    if current_user.id != user_id:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authorized to update this user's picture")

    old_filename = current_user.image_file
    if old_filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No profile picture to delete")

    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)

    return current_user
