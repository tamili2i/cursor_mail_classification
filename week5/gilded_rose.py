# -*- coding: utf-8 -*-

class Item:
    def __init__(self, name, sell_in, quality):
        print(f"DEBUG: Creating Item: name={name}, sell_in={sell_in}, quality={quality}")
        if not isinstance(name, str):
            raise TypeError("Item name must be a string")
        if not isinstance(sell_in, int):
            raise TypeError("sell_in must be an integer")
        if not isinstance(quality, int):
            raise TypeError("quality must be an integer")
        if quality < 0 or quality > 50:
            raise ValueError("Quality must be between 0 and 50")
        self.name = name
        self.sell_in = sell_in
        self.quality = quality

    def __repr__(self):
        return "%s, %s, %s" % (self.name, self.sell_in, self.quality)

class ItemUpdater:
    def update(self, item):
        raise NotImplementedError

class NormalItemUpdater(ItemUpdater):
    def update(self, item):
        print(f"DEBUG: NormalItemUpdater: Before update: {item}")
        if not hasattr(item, 'quality') or not hasattr(item, 'sell_in'):
            raise AttributeError("Item missing required attributes")
        if item.quality > 0:
            item.quality -= 1
        item.sell_in -= 1
        if item.sell_in < 0 and item.quality > 0:
            item.quality -= 1
        item.quality = max(0, min(50, item.quality))
        print(f"DEBUG: NormalItemUpdater: After update: {item}")

class AgedBrieUpdater(ItemUpdater):
    def update(self, item):
        print(f"DEBUG: AgedBrieUpdater: Before update: {item}")
        if not hasattr(item, 'quality') or not hasattr(item, 'sell_in'):
            raise AttributeError("Item missing required attributes")
        if item.quality < 50:
            item.quality += 1
        item.sell_in -= 1
        if item.sell_in < 0 and item.quality < 50:
            item.quality += 1
        item.quality = max(0, min(50, item.quality))
        print(f"DEBUG: AgedBrieUpdater: After update: {item}")

class BackstagePassUpdater(ItemUpdater):
    def update(self, item):
        print(f"DEBUG: BackstagePassUpdater: Before update: {item}")
        if not hasattr(item, 'quality') or not hasattr(item, 'sell_in'):
            raise AttributeError("Item missing required attributes")
        if item.quality < 50:
            item.quality += 1
            if item.sell_in < 11 and item.quality < 50:
                item.quality += 1
            if item.sell_in < 6 and item.quality < 50:
                item.quality += 1
        item.sell_in -= 1
        if item.sell_in < 0:
            item.quality = 0
        item.quality = max(0, min(50, item.quality))
        print(f"DEBUG: BackstagePassUpdater: After update: {item}")

class SulfurasUpdater(ItemUpdater):
    def update(self, item):
        print(f"DEBUG: SulfurasUpdater: No update needed for: {item}")
        # Legendary item, does not change
        pass

def get_updater(item):
    if not hasattr(item, 'name'):
        raise AttributeError("Item missing 'name' attribute")
    if item.name == "Aged Brie":
        return AgedBrieUpdater()
    elif item.name == "Backstage passes to a TAFKAL80ETC concert":
        return BackstagePassUpdater()
    elif item.name == "Sulfuras, Hand of Ragnaros":
        return SulfurasUpdater()
    elif item.name:  # Defensive: fallback for known items
        return NormalItemUpdater()
    else:
        raise ValueError(f"Unknown item type: {item}")

class GildedRose(object):
    def __init__(self, items):
        self.items = items

    def update_quality(self):
        print("DEBUG: Starting update_quality for all items")
        for idx, current_item in enumerate(self.items):
            print(f"DEBUG: Updating item {idx}: {current_item}")
            try:
                updater = get_updater(current_item)
                updater.update(current_item)
                print(f"DEBUG: Updated item {idx}: {current_item}")
            except Exception as e:
                print(f"ERROR: Failed to update item {idx} ({current_item}): {e}")
        print("DEBUG: Finished update_quality for all items")
