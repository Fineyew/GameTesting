# Godot gameplay modules

Client modules should mirror backend module boundaries:

- `InventoryClient`
- `QuestClient`
- `CombatClient`
- `SocialClient`
- `ShopClient`
- `CraftingClient`

Each module should receive explicit dependencies such as `ApiClient` or `ContentRepository` during construction. Avoid calling autoloads directly from UI/gameplay modules, and avoid hardcoding gameplay content, quest objectives, spell math, shop listings, or loot rules in GDScript.
