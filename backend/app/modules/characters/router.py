from fastapi import APIRouter

router = APIRouter()


@router.get("/module-status")
async def module_status() -> dict[str, str]:
    return {
        "module": "characters",
        "status": "scaffold",
        "boundary": "character identity, progression, zone position",
    }
