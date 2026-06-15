from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ModuleDescriptor:
    key: str
    owner: str
    status: str
    owns: tuple[str, ...]
    allowed_dependencies: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


MODULES: tuple[ModuleDescriptor, ...] = (
    ModuleDescriptor(
        key="auth",
        owner="accounts",
        status="planned",
        owns=("accounts", "credentials", "refresh_tokens", "sessions"),
    ),
    ModuleDescriptor(
        key="characters",
        owner="characters",
        status="scaffold",
        owns=("character_profile", "progression", "zone_position"),
        allowed_dependencies=("content",),
    ),
    ModuleDescriptor(
        key="content",
        owner="content",
        status="scaffold",
        owns=("content_definitions", "content_manifest", "content_validation"),
    ),
    ModuleDescriptor(
        key="inventory",
        owner="inventory",
        status="scaffold",
        owns=("item_instances", "wallets", "equipment_slots"),
        allowed_dependencies=("content",),
    ),
    ModuleDescriptor(
        key="quests",
        owner="quests",
        status="scaffold",
        owns=("quest_state", "objective_progress"),
        allowed_dependencies=("content", "inventory", "events"),
    ),
    ModuleDescriptor(
        key="combat",
        owner="combat",
        status="scaffold",
        owns=("combat_sessions", "turn_logs", "pending_rewards"),
        allowed_dependencies=("content", "characters", "inventory", "loot", "events"),
    ),
    ModuleDescriptor(
        key="social",
        owner="social",
        status="scaffold",
        owns=("friends", "parties", "guilds", "chat", "trades", "mail"),
        allowed_dependencies=("characters", "inventory", "events"),
    ),
    ModuleDescriptor(
        key="vertical_slice",
        owner="vertical_slice",
        status="implemented",
        owns=("starter_account_loop", "starter_character_loop", "starter_world_progress"),
        allowed_dependencies=("content",),
    ),
)


def module_registry() -> list[dict[str, object]]:
    return [module.to_dict() for module in MODULES]
