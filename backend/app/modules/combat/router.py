from fastapi import APIRouter

router = APIRouter()


@router.get("/module-status")
async def module_status() -> dict[str, str]:
    return {
        "module": "combat",
        "status": "scaffold",
        "boundary": "server-authoritative turn sessions and action logs",
    }
