"""Small catalog-owned inventory/equipment rules; no persistence or client stat inputs."""
from backend.app.modules.contracts import ContentReader


class InventoryRules:
    def __init__(self, catalog: ContentReader):
        self.items = {d.key: d for d in catalog.list_definitions() if d.type in {"items", "equipment"}}
        self.shops = {d.key: d for d in catalog.list_definitions("shops")}

    def shop(self, key):
        if not isinstance(key, str) or key not in self.shops:
            raise ValueError("shop is unavailable")
        return self.shops[key]

    def equipment(self, character, slot, item_key):
        if slot != "chest":
            raise ValueError("unknown equipment slot")
        item = self.items.get(item_key) if isinstance(item_key, str) else None
        if not item or item.type != "equipment" or item.rules["slot"] != slot:
            raise ValueError("invalid equipment item")
        if character.inventory.get(item_key, 0) < 1:
            raise ValueError("character does not own that equipment")
        if character.level < item.rules["required_level"]:
            raise ValueError("character level is too low")
        return item

    def guard(self, character):
        # Revalidate ownership/slot/level even for persisted state. No stored stat authority.
        return sum(m["value"] for slot, key in character.equipment.items()
                   for m in self.equipment(character, slot, key).rules["modifiers"])

    def item_view(self, character, key):
        item = self.items[key]
        view = {"item_key": key, "name": item.display.name, "summary": item.display.summary,
                "type": item.type, "owned": character.inventory.get(key, 0)}
        if item.type == "equipment":
            slot = item.rules["slot"]
            current = character.equipment.get(slot)
            guard = sum(m["value"] for m in item.rules["modifiers"])
            current_guard = self.guard(character)
            view.update(slot=slot, required_level=item.rules["required_level"], guard=guard,
                        current_guard=current_guard, guard_delta=guard-current_guard,
                        equipped=current == key, equipped_name=self.items[current].display.name if current else "No chest equipment")
        return view

    def inventory_view(self, character):
        return {"character": character.public_state(), "stats": {"guard": self.guard(character)},
                "items": [self.item_view(character, key) for key in sorted(character.inventory) if key in self.items and character.inventory[key] > 0]}

    def shop_view(self, character, shop_key):
        shop = self.shop(shop_key)
        listings = []
        for listing in shop.rules["listings"]:
            item = self.item_view(character, listing["item_key"])
            reason = listing.get("unavailable_reason", "Unavailable") if not listing["available"] else ""
            limit = self.items[listing["item_key"]].rules["stack_limit"]
            if not reason and item["owned"] + listing["quantity"] > limit:
                reason = "Already owned" if item["type"] == "equipment" else "Stack is full"
            if not reason and character.level < item.get("required_level", 1):
                reason = "Requires level %s" % item["required_level"]
            price = listing["price"][0]["amount"]
            if not reason and character.wallet.get("shell_chits", 0) < price:
                reason = "Not enough shell chits"
            listings.append({**item, "listing_key": listing["key"], "quantity": listing["quantity"],
                             "price": price, "can_buy": not reason, "reason": reason})
        return {**self.inventory_view(character), "shop": {"key": shop.key, "name": shop.display.name,
                "version": shop.version, "listings": listings}}

    def purchase(self, character, shop_key, listing_key, quantity, shop_version):
        shop = self.shop(shop_key)
        if shop.version != shop_version:
            raise ValueError("shop changed; reload prices before buying")
        listing = next((row for row in shop.rules["listings"] if row["key"] == listing_key), None)
        if not listing or not listing["available"]:
            raise ValueError("item is not available from this shop")
        item = self.items[listing["item_key"]]
        if character.level < item.rules.get("required_level", 1):
            raise ValueError("character level is too low")
        count = quantity * listing["quantity"]
        owned = character.inventory.get(item.key, 0)
        if owned + count > item.rules["stack_limit"]:
            raise ValueError("already owned or inventory stack would be full")
        total = quantity * listing["price"][0]["amount"]
        balance = character.wallet.get("shell_chits", 0)
        if balance < total:
            raise ValueError("not enough shell chits")
        character.wallet["shell_chits"] = balance - total
        character.inventory[item.key] = owned + count
        return {"item_key": item.key, "quantity": count, "spent": total, "currency_key": "shell_chits"}
