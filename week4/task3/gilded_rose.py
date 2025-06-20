# -*- coding: utf-8 -*-

class Item:
    def __init__(self, name, sell_in, quality):
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
        if item.quality > 0:
            item.quality -= 1
        item.sell_in -= 1
        if item.sell_in < 0 and item.quality > 0:
            item.quality -= 1

class AgedBrieUpdater(ItemUpdater):
    def update(self, item):
        if item.quality < 50:
            item.quality += 1
        item.sell_in -= 1
        if item.sell_in < 0 and item.quality < 50:
            item.quality += 1

class BackstagePassUpdater(ItemUpdater):
    def update(self, item):
        if item.quality < 50:
            item.quality += 1
            if item.sell_in < 11 and item.quality < 50:
                item.quality += 1
            if item.sell_in < 6 and item.quality < 50:
                item.quality += 1
        item.sell_in -= 1
        if item.sell_in < 0:
            item.quality = 0

class SulfurasUpdater(ItemUpdater):
    def update(self, item):
        # Legendary item, does not change
        pass

def get_updater(item):
    if item.name == "Aged Brie":
        return AgedBrieUpdater()
    elif item.name == "Backstage passes to a TAFKAL80ETC concert":
        return BackstagePassUpdater()
    elif item.name == "Sulfuras, Hand of Ragnaros":
        return SulfurasUpdater()
    else:
        return NormalItemUpdater()

class GildedRose(object):
    def __init__(self, items):
        self.items = items

    def update_quality(self):
        for item in self.items:
            updater = get_updater(item)
            updater.update(item)
