from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import os, json, time
from pathlib import Path

DATA_DIR = Path("../data")
POSTS_DIR = DATA_DIR / "posts"
POSTS_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_KEY = os.environ.get("ADMIN_KEY", "changeme")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/posts")
def list_posts():
    posts = []
    for file in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        with open(file, "r") as f:
            posts.append(json.load(f))
    return posts

@app.get("/posts/{ts}")
def get_post(ts: str):
    file = POSTS_DIR / f"{ts}.json"
    if not file.exists():
        raise HTTPException(404)
    return json.load(open(file))

@app.post("/new")
def new_post(
    title: str,
    content: str,
    persona: str = "Clove",
    x_admin_key: str =Header(None)
):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(401, "invalid admin key")
    
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")

    post = {
        "timestamp": timestamp,
        "title": title,
        "persona": persona,
        "content": content,
    }

    with open(POSTS_DIR / f"{timestamp}.json", "w") as f:
        json.dump(post, f, indent=2)

    return {"status": "ok", "timestamp": timestamp}