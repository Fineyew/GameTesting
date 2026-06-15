# Godot gameplay modules

Client modules should mirror backend module boundaries:

- `InventoryClient`
- `QuestClient`
- `CombatClient`
- `SocialClient`
- `ShopClient`
- `CraftingClient`

Each module should call `ApiClient` and consume definitions through `ContentCache`. Avoid hardcoding gameplay content, quest objectives, spell math, shop listings, or loot rules in GDScript.
