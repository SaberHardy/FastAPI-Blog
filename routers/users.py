from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostResponse, UserCreate, UserPublic, UserPrivate, UserUpdate, TokenSchema
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from auth import create_access_token, hash_password, verify_access_token, verify_password, oauth_scheme
from config import settings

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
async def get_current_user(token: Annotated[str, Depends(oauth_scheme)], db: Annotated[AsyncSession, Depends(get_db)]):
    """Get the currently authenticated user."""
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})

    # Validate user_id is a valid integer (defense against malformed JWT)
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})

    result = await db.execute(select(models.User).where(models.User.id == user_id_int))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


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
async def update_user(user_id: int, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
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

    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User Not Found")

    await db.delete(user)
    await db.commit()
