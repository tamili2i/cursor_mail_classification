# Gilded Rose Refactored

## Overview

This implementation refactors the classic Gilded Rose kata to improve maintainability, testability, and extensibility. The update logic for each item type is separated using polymorphism, following the Single Responsibility Principle. Each item type has its own updater class, making it easy to add new item types or modify existing rules.

## Design Principles

- **Single Responsibility Principle:** Each updater class handles only one item type's update logic.
- **Polymorphism:** The main update loop delegates to the correct updater, eliminating complex conditional logic.
- **Validation:** The `Item` class validates quality boundaries.
- **Extensibility:** Adding new item types is as simple as creating a new updater class and updating the `get_updater` function.

## Class Responsibilities

- **Item:** Represents an item with `name`, `sell_in`, and `quality`. Validates quality on creation.
- **ItemUpdater (abstract):** Base class for all updaters. Defines the `update(item)` interface.
- **NormalItemUpdater:** Handles standard item update rules.
- **AgedBrieUpdater:** Handles rules for "Aged Brie".
- **BackstagePassUpdater:** Handles rules for "Backstage passes to a TAFKAL80ETC concert".
- **SulfurasUpdater:** Handles rules for "Sulfuras, Hand of Ragnaros" (legendary, does not change).
- **get_updater:** Factory function that returns the correct updater for a given item.
- **GildedRose:** Main class that manages the list of items and delegates updates.

## Usage Example

```python
items = [
    Item("Aged Brie", 2, 0),
    Item("Backstage passes to a TAFKAL80ETC concert", 15, 20),
    Item("Sulfuras, Hand of Ragnaros", 0, 80),
    Item("Normal Item", 10, 20)
]
gilded_rose = GildedRose(items)
gilded_rose.update_quality()
for item in items:
    print(item)
```

## Extending for New Item Types

To add a new item type:
1. Create a new updater class inheriting from `ItemUpdater`.
2. Implement the `update(self, item)` method with the new rules.
3. Update the `get_updater(item)` function to return your new updater for the appropriate item name.

## Testing

- Each updater can be tested in isolation.
- Edge cases (quality at 0/50, sell_in at 0/-1) should be covered.
- "Sulfuras" should never change.
- "Backstage passes" should drop to 0 after the concert.

## Benefits

- No function longer than 20 lines.
- Each function/class has a single responsibility.
- Improved readability and maintainability.
- Easy to add or modify item types. 