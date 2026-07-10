from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, blog, daily, flashcards, learn, oauth, search
from app.routers.admin import articles as admin_articles
from app.routers.admin import dashboard as admin_dashboard
from app.routers.admin import lessons as admin_lessons
from app.routers.admin import vocabulary as admin_vocabulary

app = FastAPI(title="Heniiii API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(learn.router)
app.include_router(daily.router)
app.include_router(flashcards.router)
app.include_router(blog.router)
app.include_router(search.router)
app.include_router(admin_lessons.router)
app.include_router(admin_vocabulary.router)
app.include_router(admin_articles.router)
app.include_router(admin_dashboard.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
