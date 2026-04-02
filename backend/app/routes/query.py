from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from openai import RateLimitError, AuthenticationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.openai_service import handle_query
from app.db.connection import get_db

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class QueryRequest(BaseModel):
    message: str
    location: str | None = None       # e.g. "CDS", "CAS", "GSU"
    time_available: int | None = None  # minutes
    interests: list[str] | None = None


@router.post("/query")
@limiter.limit("10/day")
async def query(request: Request, req: QueryRequest, db=Depends(get_db)):
    try:
        result = await handle_query(
            message=req.message,
            location=req.location,
            time_available=req.time_available,
            interests=req.interests,
            db=db,
        )
        return result
    except RateLimitError:
        raise HTTPException(
            status_code=402,
            detail="OpenAI quota exceeded. Add billing credits at platform.openai.com/billing.",
        )
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
