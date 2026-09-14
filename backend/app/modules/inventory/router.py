from fastapi import APIRouter

router = APIRouter()


@router.get("/module-status")
async def module_status() -> dict[str, str]:
    return {
        "module": "inventory",
        "status": "implemented_narrow_slice",
        "boundary": "item instances, equipment loadouts, wallets",
    }
