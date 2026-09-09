import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
import logging
import math
import time
from backend.app.modules.world.simulation import step

logger = logging.getLogger(__name__)
PHRASES = {"hello": "Hello, Wayfarer!", "help": "Could you lend a light?", "thanks": "Thank you!", "follow": "Let's explore together.", "farewell": "Safe tides!"}


@dataclass
class Presence:
    socket: object
    account_id: str
    character_id: str
    name: str
    appearance: dict
    expires: float
    position: list
    axis: list = field(default_factory=lambda: [0.0, 0.0])
    velocity: list = field(default_factory=lambda: [0.0, 0.0])
    seq: int = -1
    seen: float = field(default_factory=time.monotonic)
    last_packet: float = 0
    chat_at: float = 0
    in_combat: bool = False
    bubble: str = ""
    bubble_until: float = 0


class WorldHub:
    def __init__(self, geometry, players):
        self.geometry, self.players = geometry, players
        self.members = {}
        self.task = None
        self.tick = 0

    def start(self):
        self.task = asyncio.create_task(self._loop())

    async def join(self, member):
        old = self.members.get(member.character_id)
        if old:
            member.position = list(old.position)
            self.members[member.character_id] = member
            with suppress(Exception):
                await old.socket.close(code=4001, reason="connected elsewhere")
        else:
            if len(self.members) >= 32:
                raise ValueError("Dawnreef is full; try again shortly")
            self.members[member.character_id] = member

    async def leave(self, member):
        if self.members.get(member.character_id) is not member:
            return
        del self.members[member.character_id]
        try:
            await asyncio.to_thread(self._save, member)
        except Exception:
            logger.exception("world_checkpoint_failed", extra={"character_id": member.character_id})
        with suppress(Exception):
            await member.socket.close()

    def _save(self, member):
        with self.players.store.transaction(member.character_id):
            character = self.players._require_character(member.account_id, member.character_id)
            character.position = {"x": member.position[0], "z": member.position[1]}
            self.players.store.save_character(character)

    def near(self, character_id, target, distance=3.5):
        member = self.members.get(character_id)
        at = self.geometry["interactions"].get(target)
        return bool(member and at and math.dist(member.position, at) <= distance)

    def receive(self, member, message):
        if self.members.get(member.character_id) is not member:
            raise ValueError("session replaced")
        now = time.monotonic()
        member.seen = now
        if message.get("type") == "ping":
            return
        if message.get("type") == "move":
            axis, seq = message.get("axis"), message.get("seq")
            if not isinstance(axis, list) or len(axis) != 2 or any(type(v) not in (float, int) or not math.isfinite(v) or abs(v) > 1 for v in axis):
                raise ValueError("invalid movement")
            if type(seq) is not int or not 0 <= seq < 2**31:
                raise ValueError("invalid sequence")
            if seq <= member.seq or now - member.last_packet < .025:
                return
            member.seq, member.axis, member.last_packet = seq, axis, now
        elif message.get("type") == "say":
            phrase = message.get("phrase")
            if phrase not in PHRASES:
                raise ValueError("unknown phrase")
            if now - member.chat_at >= 2:
                member.bubble, member.chat_at, member.bubble_until = PHRASES[phrase], now, now + 5
        else:
            raise ValueError("unknown world message")

    async def disconnect_account(self, account_id):
        for member in list(self.members.values()):
            if member.account_id == account_id:
                with suppress(Exception):
                    await member.socket.close(code=4003, reason="session ended")
                await self.leave(member)

    async def _send(self, member, frame):
        try:
            await asyncio.wait_for(member.socket.send_json(frame), .5)
        except Exception:
            await self.leave(member)

    async def _loop(self):
        while True:
            started = time.monotonic()
            self.tick += 1
            for member in list(self.members.values()):
                if started - member.seen > 20 or time.time() >= member.expires:
                    await self.leave(member)
                    continue
                axis = [0, 0] if started - member.last_packet > .4 or member.in_combat else member.axis
                member.position, member.velocity = step(member.position, member.velocity, axis, .05, self.geometry)
            if self.tick % 2 == 0:
                frame = {"type": "snapshot", "protocol": 1, "tick": self.tick, "players": [
                    {"id": m.character_id, "name": m.name, "appearance": m.appearance,
                     "x": m.position[0], "z": m.position[1], "seq": m.seq,
                     "bubble": m.bubble if started < m.bubble_until else ""} for m in self.members.values()]}
                await asyncio.gather(*(self._send(m, frame) for m in list(self.members.values())))
            if self.tick % 100 == 0:
                for member in list(self.members.values()):
                    try:
                        await asyncio.to_thread(self._save, member)
                    except Exception:
                        logger.exception("world_checkpoint_failed", extra={"character_id": member.character_id})
            await asyncio.sleep(max(0, .05 - (time.monotonic() - started)))

    async def stop(self):
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        for member in list(self.members.values()):
            await self.leave(member)
