from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    score: int


class LeaderboardResponse(BaseModel):
    scope: str
    lang: str | None
    entries: list[LeaderboardEntry]
