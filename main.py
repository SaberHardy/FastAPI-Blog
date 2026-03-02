from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


@app.get("/", include_in_schema=False)
@app.get("/posts", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})

@app.get("/api/posts")
def get_posts():
    return {"posts": posts}

@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return {"post": post}
    return {"message": "Post not found"}
