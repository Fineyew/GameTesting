from fastapi import APIRouter

router = APIRouter()


@router.get("/module-status")
async def module_status() -> dict[str, str]:
    return {
        "module": "quests",
        "status": "scaffold",
        "boundary": "accepted quests, objectives, completion rewards via ports",
    }
