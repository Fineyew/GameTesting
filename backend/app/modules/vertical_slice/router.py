from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.app.core.security import decode_access_token
from backend.app.modules.vertical_slice.service import (
    AuthenticationError,
    NotFoundError,
    VerticalSliceError,
    VerticalSliceService,
)

router = APIRouter(tags=["vertical-slice"])


class RegisterRequest(BaseModel):
    email: str
    display_name: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateCharacterRequest(BaseModel):
    name: str
    ancestry_key: str = "lumenfolk"
    origin_key: str = "dawnreef_local"


class FightRequest(BaseModel):
    enemy_key: str
    spell_key: str


def get_vertical_slice_service(request: Request) -> VerticalSliceService:
    return request.app.state.vertical_slice_service


def current_account_id(authorization: str = Header(default="")) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token subject")
    return subject


@router.post("/auth/register")
async def register(
    payload: RegisterRequest,
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.register(payload.email, payload.display_name, payload.password).public_state()
    except VerticalSliceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/auth/login")
async def login(
    payload: LoginRequest,
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.login(payload.email, payload.password).public_state()
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/auth/logout")
async def logout(
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, str]:
    return service.logout(account_id)


@router.post("/characters")
async def create_character(
    payload: CreateCharacterRequest,
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.create_character(
            account_id=account_id,
            name=payload.name,
            ancestry_key=payload.ancestry_key,
            origin_key=payload.origin_key,
        ).public_state()
    except VerticalSliceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/characters")
async def list_characters(
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> list[dict[str, Any]]:
    return [character.public_state() for character in service.list_characters(account_id)]


@router.get("/world/characters/{character_id}")
async def enter_world(
    character_id: str,
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.enter_world(account_id, character_id).public_state()
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/world/characters/{character_id}/quests/{quest_key}/accept")
async def accept_quest(
    character_id: str,
    quest_key: str,
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.accept_quest(account_id, character_id, quest_key).public_state()
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerticalSliceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/world/characters/{character_id}/combat/fight")
async def fight_enemy(
    character_id: str,
    payload: FightRequest,
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.fight_enemy(
            account_id=account_id,
            character_id=character_id,
            enemy_key=payload.enemy_key,
            spell_key=payload.spell_key,
        ).public_state()
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerticalSliceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/world/characters/{character_id}/save")
async def save_progress(
    character_id: str,
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.save_progress(account_id, character_id).public_state()
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
