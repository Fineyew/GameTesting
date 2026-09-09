import asyncio
import json
from contextlib import suppress
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.security import decode_access_token
from backend.app.modules.world.hub import Presence

router = APIRouter()


@router.websocket("/world/socket")
async def world_socket(socket: WebSocket):
    await socket.accept()
    member = None
    hub = socket.app.state.world_hub
    players = socket.app.state.vertical_slice_service
    try:
        raw = await asyncio.wait_for(socket.receive_text(), 5)
        if len(raw) > 4096:
            raise ValueError("authentication too large")
        message = json.loads(raw)
        if not isinstance(message, dict) or message.get("type") != "auth" or message.get("protocol") != 1:
            raise ValueError("unsupported world protocol")
        claims = decode_access_token(message["token"])
        account_id = await asyncio.to_thread(players.validate_session, claims)
        character = await asyncio.to_thread(players.enter_world, account_id, message["character_id"])
        member = Presence(socket, account_id, character.id, character.name, character.appearance, claims["exp"], [character.position["x"], character.position["z"]])
        member.in_combat = character.encounter.get("state") == "active"
        await hub.join(member)
        await socket.send_json({"type": "welcome", "protocol": 1, "character_id": character.id})
        while True:
            raw = await asyncio.wait_for(socket.receive_text(), 20)
            if len(raw) > 1024:
                raise ValueError("packet too large")
            hub.receive(member, json.loads(raw))
    except (ValueError, KeyError, TypeError, AttributeError):
        with suppress(Exception):
            await socket.close(code=4003, reason="invalid or expired session")
    except (WebSocketDisconnect, TimeoutError):
        pass
    finally:
        if member:
            await hub.leave(member)
