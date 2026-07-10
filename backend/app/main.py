from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, daily, flashcards, learn, oauth
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
app.include_router(admin_lessons.router)
app.include_router(admin_vocabulary.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
