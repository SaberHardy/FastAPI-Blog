from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate
import models
from auth import CurrentUser

router = APIRouter()


@router.get("/{post_id}", response_model=list[PostResponse])
async def get_post(db: Annotated[AsyncSession, Depends(get_db)], post_id: int):
    post = await db.execute(select(models.Post).where(models.Post.id == post_id)).scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


# @router.get("", response_model=list[PostResponse])
# async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
#     posts = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
#
#     if posts:
#         return posts
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posts not found")


@router.get("", response_model=list[PostResponse])
async def get_all_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    posts = await db.execute(select(models.Post).options(selectinload(models.Post.author))
                             .order_by(models.Post.date_posted.desc()))
    all_posts = posts.scalars().all()
    return all_posts


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    """This is commented out bcz of the CurrentUser added and this will be handled there"""
    # result = await db.execute(select(models.User).where(models.User.id == post.user_id))
    # user = result.scalars().first()
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_post = models.Post(title=post.title, content=post.content, user_id=current_user.id)

    db.add(new_post)

    await db.commit()
    # when we create new post we need to refresh the author name in the database (load with specific relationship)
    await db.refresh(new_post, attribute_names=["author"])
    return new_post


@router.put("/{post_id}", response_model=PostResponse)
def update_post_full(post_id: int, post_data: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = results.scalars().first()
    print(f"This is the post we are printing: {post}")

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Fount")

    if post_data.user_id != post.user_id:
        results = db.execute(select(models.User).where(models.User.id == post_data.user_id))
        user = results.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")

    post.title = post_data.title
    post.content = post_data.content
    post.used_id = post_data.user_id

    db.commit()
    db.refresh(post, attribute_names=["author"])

    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    print(f"This is the post we are printing: {post}")

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Fount")

    update_data = post_data.model_dump(exclude_unset=True)
    print(f"Update data is: {update_data}")

    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    print(f"The updated post is: {post}")
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = results.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Fount")

    await db.delete(post)
    await db.commit()
