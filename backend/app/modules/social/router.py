from fastapi import APIRouter

router = APIRouter()


@router.get("/module-status")
async def module_status() -> dict[str, str]:
    return {
        "module": "social",
        "status": "scaffold",
        "boundary": "friends, parties, guilds, chat, trades, and mail",
    }
