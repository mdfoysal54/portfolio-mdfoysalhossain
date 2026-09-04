from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.orchestrator import evu_agent
from app.agent.schemas import AgentRequest, AgentResponse
from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User


router = APIRouter(prefix="/api/v1/agent", tags=["EVU Agent"])


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await evu_agent.run(request, current_user, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"EVU agent error: {exc}") from exc
