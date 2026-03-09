class FoodItem:
    def __init__(self, name: str, price: float, category: str, popularity_rating: float):
        self.name = name
        self.price = price
        self.category = category
        self.popularity_rating = popularity_rating


class Menu:
    def __init__(self):
        self.items: list[FoodItem] = []

    def add_item(self, item: FoodItem) -> None:
        self.items.append(item)

    def filter_by_category(self, category: str) -> list[FoodItem]:
        return [item for item in self.items if item.category.lower() == category.lower()]

    def sort_by_price(self, ascending: bool = True) -> list[FoodItem]:
        return sorted(self.items, key=lambda item: item.price, reverse=not ascending)

    def sort_by_popularity(self, ascending: bool = False) -> list[FoodItem]:
        return sorted(self.items, key=lambda item: item.popularity_rating, reverse=not ascending)


class Transaction:
    def __init__(self):
        self.items: list[FoodItem] = []

    def add_item(self, item: FoodItem) -> None:
        self.items.append(item)

    def get_item_count(self) -> int:
        return len(self.items)

    def compute_total(self) -> float:
        return sum(item.price for item in self.items)


class Customer:
    def __init__(self, name: str):
        self.name = name
        self.purchase_history: list[Transaction] = []

    def add_transaction(self, transaction: Transaction) -> None:
        self.purchase_history.append(transaction)

    def get_total_spent(self) -> float:
        return sum(t.compute_total() for t in self.purchase_history)

    def is_verified(self) -> bool:
        return bool(self.name and self.purchase_history)
