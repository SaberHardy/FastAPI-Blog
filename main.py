from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import PostResponse, PostCreate, UserResponse, UserCreate, PostUpdate, UserUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated

import models
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()

    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})


@app.get("/api/posts", response_model=list[PostResponse])
def get_all_posts(db: Annotated[Session, Depends(get_db)]):
    all_posts = db.execute(select(models.Post)).scalars().all()
    return all_posts


@app.post("/api/posts", response_model=PostResponse)
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User Not Found")

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()

    return posts


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(db: Annotated[Session, Depends(get_db)], post_id: int):
    post = db.execute(select(models.Post).where(models.Post.id == post_id)).scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(post_id: int, post_data: PostCreate, db: Annotated[Session, Depends(get_db)]):
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
    db.refresh(post)

    return post


@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_partial(post_id: int, post_data: PostUpdate, db: Annotated[Session, Depends(get_db)]):
    results = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = results.scalars().first()
    print(f"This is the post we are printing: {post}")

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Fount")

    update_data = post_data.model_dump(exclude_unset=True)
    print(f"Update data is: {update_data}")

    for field, value in update_data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    print(f"The updated post is: {post}")
    return post


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    results = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = results.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Fount")

    db.delete(post)
    db.commit()


@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    existing_email = db.execute(
        select(models.User).where(models.User.email == user.email)).scalars().first()  # first obj or none if not exist
    existing_user = db.execute(select(models.User).where(models.User.username == user.username)).scalars().first()


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):  # get single post from the page
    results = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = results.scalars().first()

    if post:
        title = post.title[:50]
        return templates.TemplateResponse(request, "post_details.html", {"post": post, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    new_user = models.User(username=user.username, email=user.email)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # this will refresh the new_user object with the data from the database

    # When we return this Pydantic automatic returns UserResponse because we specified it in the response_model,
    # and it will read the data from the new_user object because we set from_attributes=True in the UserResponse model_config
    return new_user


@app.post("api/users/{user_id}", response_model=UserResponse)  # , status_code=status.HTTP_201_CREATED)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.username is not None and user_update.username != user.username:
        result = db.execute(select(models.User).where(models.User.username == user_update.username))
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User name already exists")

    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(select(models.User).where(models.User.email == user_update.email))
        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User name already exists")

    # After the validation, i can update only the fields are provided
    if user_update.username is not None:
        user.user_name = user_update.username

    if user_update.email is not None:
        user.email = user_update.email

    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    db.commit()
    db.refresh(user)

    return user


@app.post("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(request: Request, user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User Not Found")

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()

    return templates.TemplateResponse(request, "user_posts.html",
                                      {"posts": posts,
                                       "user": user,
                                       "title": f"{user.username}'s Posts"})


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    selected_user = db.execute(select(models.User).where(models.User.id == post.user_id))
    user_to_create_post = selected_user.scalars().first()

    if not user_to_create_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")

    new_post = models.Post(title=post.title, content=post.content, user_id=post.user_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):  # get single post from the page
    results = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = results.scalars().first()

    if post:
        title = post.title[:50]
        return templates.TemplateResponse(request, "post_details.html", {"post": post, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


# ========================
# EXCEPTION HANDLERS
# ========================


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exc: StarletteHTTPException):
    message = (exc.detail if exc.detail else "An error occurred on the server side.")
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exc.status_code, content={"detail": message})
    return templates.TemplateResponse(request,
                                      "error_page.html",
                                      {
                                          "title": exc.status_code,
                                          "message": message,
                                          "status_code": exc.status_code
                                      },
                                      status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            content={"detail": exception.errors()})
    return templates.TemplateResponse(request,
                                      "error_page.html",
                                      {
                                          "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
                                          "message": exception.errors(),
                                          "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
                                      },
                                      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
