from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "author": "Liam Carter",
        "title": "Exploring Microservices Architecture",
        "content": "Microservices allow teams to build scalable and maintainable systems by breaking applications into smaller, independent services.",
        "date_posted": "2026-02-12T09:15:23Z"
    },
    {
        "id": 2,
        "author": "Sophia Martinez",
        "title": "Introduction to Data Pipelines",
        "content": "Data pipelines automate the movement and transformation of data between systems, enabling efficient analytics and reporting.",
        "date_posted": "2026-02-14T14:42:10Z"
    },
    {
        "id": 3,
        "author": "Noah Thompson",
        "title": "Understanding RESTful APIs",
        "content": "RESTful APIs use standard HTTP methods to enable communication between clients and servers in a stateless manner.",
        "date_posted": "2026-02-18T08:30:45Z"
    },
    {
        "id": 4,
        "author": "Emma Johnson",
        "title": "Scaling Applications with Kubernetes",
        "content": "Kubernetes helps manage containerized applications, providing automated deployment, scaling, and operations.",
        "date_posted": "2026-02-22T17:05:12Z"
    },
    {
        "id": 5,
        "author": "Oliver Brown",
        "title": "Getting Started with Machine Learning",
        "content": "Machine learning enables systems to learn from data and improve performance without being explicitly programmed.",
        "date_posted": "2026-02-25T11:20:37Z"
    }
]


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})


@app.get("/api/posts")
def get_posts():
    return {"posts": posts}


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            title: str = post["title"][:50]
            return templates.TemplateResponse(request,
                                              "post_details.html",
                                              {"post": post, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return {"post": post}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


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
