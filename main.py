from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import PostResponse, PostCreate, UserResponse, UserCreate
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


# posts: list[dict] = [
#     {
#         "id": 1,
#         "author": "Liam Carter",
#         "title": "Exploring Microservices Architecture",
#         "content": "Microservices allow teams to build scalable and maintainable systems by breaking applications into smaller, independent services.",
#         "date_posted": "2026-02-12T09:15:23Z"
#     },
#     {
#         "id": 2,
#         "author": "Sophia Martinez",
#         "title": "Introduction to Data Pipelines",
#         "content": "Data pipelines automate the movement and transformation of data between systems, enabling efficient analytics and reporting.",
#         "date_posted": "2026-02-14T14:42:10Z"
#     },
#     {
#         "id": 3,
#         "author": "Noah Thompson",
#         "title": "Understanding RESTful APIs",
#         "content": "RESTful APIs use standard HTTP methods to enable communication between clients and servers in a stateless manner.",
#         "date_posted": "2026-02-18T08:30:45Z"
#     },
#     {
#         "id": 4,
#         "author": "Emma Johnson",
#         "title": "Scaling Applications with Kubernetes",
#         "content": "Kubernetes helps manage containerized applications, providing automated deployment, scaling, and operations.",
#         "date_posted": "2026-02-22T17:05:12Z"
#     },
#     {
#         "id": 5,
#         "author": "Oliver Brown",
#         "title": "Getting Started with Machine Learning",
#         "content": "Machine learning enables systems to learn from data and improve performance without being explicitly programmed.",
#         "date_posted": "2026-02-25T11:20:37Z"
#     }
# ]


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})


@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            title: str = post["title"][:50]
            return templates.TemplateResponse(request,
                                              "post_details.html",
                                              {"post": post, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first()  # first obj or none if not exist
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first()  # first obj or none if not exist
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    new_user = models.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # this will refresh the new_user object with the data from the database

    # When we return this Pydantic automatic returns UserResponse because we specified it in the response_model,
    # and it will read the data from the new_user object because we set from_attributes=True in the UserResponse model_config
    return new_user


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):
    import time

    new_id = max(p['id'] for p in posts) + 1 if len(posts) > 0 else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime()),
    }
    posts.append(new_post)
    return new_post


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
