from fastapi import APIRouter

from app.ai.gateway import ai_gateway


router = APIRouter(
    prefix="/api/v1/providers",
    tags=["Providers"],
)


@router.get("")
async def get_providers():
    """
    Return all EVU AI providers and their configuration status.
    """
    return ai_gateway.available_providers()