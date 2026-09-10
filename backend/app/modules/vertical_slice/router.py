from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from backend.app.core.security import decode_access_token
from backend.app.modules.vertical_slice.service import (
    AuthenticationError,
    NotFoundError,
    VerticalSliceError,
    VerticalSliceService,
)

router = APIRouter(tags=["vertical-slice"])


class RegisterRequest(BaseModel):
    email: str = Field(max_length=254)
    display_name: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class CreateCharacterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=24)
    ancestry_key: str = "lumenfolk"
    origin_key: str = "dawnreef_local"
    affinity: str = "lanterncraft"
    appearance: dict[str, str] | None = None


class FightRequest(BaseModel):
    enemy_key: str
    spell_key: str


def get_vertical_slice_service(request: Request) -> VerticalSliceService:
    return request.app.state.vertical_slice_service


def current_account_id(request: Request, authorization: str = Header(default="")) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        payload = decode_access_token(token)
        request.app.state.vertical_slice_service.validate_session(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token subject")
    return subject


@router.post("/auth/register")
def register(
    payload: RegisterRequest,
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.register(payload.email, payload.display_name, payload.password).public_state()
    except VerticalSliceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/auth/login")
def login(
    payload: LoginRequest,
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.login(payload.email, payload.password).public_state()
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/auth/logout")
async def logout(
    request: Request,
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, str]:
    import asyncio
    result = await asyncio.to_thread(service.logout, account_id)
    await request.app.state.world_hub.disconnect_account(account_id)
    return result


@router.post("/characters")
def create_character(
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
            affinity=payload.affinity,
            appearance=payload.appearance,
        ).public_state()
    except VerticalSliceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/characters")
def list_characters(
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> list[dict[str, Any]]:
    return [character.public_state() for character in service.list_characters(account_id)]


@router.get("/world/characters/{character_id}")
def enter_world(
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
def accept_quest(
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
def fight_enemy(
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
def save_progress(
    character_id: str,
    account_id: str = Depends(current_account_id),
    service: VerticalSliceService = Depends(get_vertical_slice_service),
) -> dict[str, Any]:
    try:
        return service.save_progress(account_id, character_id).public_state()
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/auth/refresh")
def refresh(account_id: str = Depends(current_account_id), service: VerticalSliceService = Depends(get_vertical_slice_service)):
    return service._auth_result(service._require_account(account_id)).public_state()


class StartEncounterRequest(BaseModel):
    enemy_key: str = Field(max_length=64)


class EncounterActionRequest(BaseModel):
    encounter_id: str = Field(max_length=40)
    action: str = Field(max_length=64)
    expected_round: int = Field(ge=1, le=50)


@router.post("/world/characters/{character_id}/encounters")
def start_encounter(character_id: str, payload: StartEncounterRequest, request: Request,
                    idempotency_key: str = Header(min_length=8, max_length=80),
                    account_id: str = Depends(current_account_id)):
    hub = request.app.state.world_hub
    try:
        if not hub.near(character_id, payload.enemy_key):
            raise ValueError("move closer to the encounter while connected")
        result = request.app.state.encounters.start(account_id, character_id, payload.enemy_key, idempotency_key)
        if character_id in hub.members:
            hub.members[character_id].in_combat = result["encounter"]["state"] == "active"
        return result
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/world/characters/{character_id}/encounters/actions")
def encounter_action(character_id: str, payload: EncounterActionRequest, request: Request,
                     idempotency_key: str = Header(min_length=8, max_length=80),
                     account_id: str = Depends(current_account_id)):
    try:
        result = request.app.state.encounters.act(account_id, character_id, payload.encounter_id,
                                                   payload.action, payload.expected_round, idempotency_key)
        member = request.app.state.world_hub.members.get(character_id)
        if member:
            member.in_combat = result["encounter"]["state"] == "active"
            if result["encounter"]["state"] == "defeat":
                member.position = [result["character"]["position"]["x"], result["character"]["position"]["z"]]
                member.velocity = [0, 0]
        return result
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


class DialogueChoiceRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=40)
    option_key: str = Field(min_length=1, max_length=64)


class PrepareFolioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spells: list[StrictStr] = Field(min_length=1, max_length=6)
    expected_revision: int = Field(strict=True, ge=0)


class PurchaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    listing_key: StrictStr = Field(min_length=1, max_length=64)
    quantity: int = Field(strict=True, ge=1, le=10)
    shop_version: int = Field(strict=True, ge=1, lt=2**31)
    expected_revision: int = Field(strict=True, ge=0, lt=2**63-1)


class EquipmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot: StrictStr = Field(min_length=1, max_length=32)
    item_key: StrictStr | None = Field(max_length=64)
    expected_revision: int = Field(strict=True, ge=0, lt=2**63-1)


def commerce_result(operation):
    try:
        return operation()
    except AuthenticationError as exc:
        raise HTTPException(403, str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/world/characters/{character_id}/shops/{shop_key}")
def shop_view(character_id: str, shop_key: str, request: Request, account_id: str = Depends(current_account_id)):
    return commerce_result(lambda: request.app.state.commerce.view(account_id, character_id, shop_key))


@router.post("/world/characters/{character_id}/shops/{shop_key}/buy")
def buy_item(character_id: str, shop_key: str, payload: PurchaseRequest, request: Request,
             idempotency_key: str = Header(min_length=8, max_length=80), account_id: str = Depends(current_account_id)):
    return commerce_result(lambda: request.app.state.commerce.buy(account_id, character_id, shop_key,
                           payload.listing_key, payload.quantity, payload.shop_version, payload.expected_revision, idempotency_key))


@router.get("/world/characters/{character_id}/equipment")
def equipment_view(character_id: str, request: Request, account_id: str = Depends(current_account_id)):
    return commerce_result(lambda: request.app.state.commerce.view(account_id, character_id))


@router.post("/world/characters/{character_id}/equipment")
def equip_item(character_id: str, payload: EquipmentRequest, request: Request,
               idempotency_key: str = Header(min_length=8, max_length=80), account_id: str = Depends(current_account_id)):
    return commerce_result(lambda: request.app.state.commerce.equip(account_id, character_id,
                           payload.slot, payload.item_key, payload.expected_revision, idempotency_key))


@router.post("/world/characters/{character_id}/folio")
def prepare_folio(character_id: str, payload: PrepareFolioRequest, request: Request,
                  idempotency_key: str = Header(min_length=8, max_length=80),
                  account_id: str = Depends(current_account_id)):
    try:
        return request.app.state.folio.prepare(account_id, character_id, payload.spells,
                                               payload.expected_revision, idempotency_key)
    except AuthenticationError as exc:
        raise HTTPException(403, str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


def require_interaction(request, account_id, character_id, target):
    # Ownership first; coordinates and node IDs supplied by clients are never trusted.
    try:
        request.app.state.vertical_slice_service._require_character(account_id, character_id)
    except AuthenticationError as exc:
        raise HTTPException(403, str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    if not request.app.state.world_hub.near(character_id, target):
        raise HTTPException(409, "move closer while connected")


@router.post("/world/characters/{character_id}/npcs/{npc_key}/dialogue")
def start_dialogue(character_id: str, npc_key: str, request: Request, account_id: str = Depends(current_account_id)):
    require_interaction(request, account_id, character_id, npc_key)
    try:
        return request.app.state.story.start(account_id, character_id, npc_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/world/characters/{character_id}/npcs/{npc_key}/dialogue/choose")
def choose_dialogue(character_id: str, npc_key: str, payload: DialogueChoiceRequest, request: Request,
                    account_id: str = Depends(current_account_id)):
    require_interaction(request, account_id, character_id, npc_key)
    try:
        return request.app.state.story.choose(account_id, character_id, npc_key, payload.conversation_id, payload.option_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/world/characters/{character_id}/interactions/{interaction_key}/inspect")
def inspect_landmark(character_id: str, interaction_key: str, request: Request, account_id: str = Depends(current_account_id)):
    require_interaction(request, account_id, character_id, interaction_key)
    try:
        return request.app.state.story.inspect(account_id, character_id, interaction_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
