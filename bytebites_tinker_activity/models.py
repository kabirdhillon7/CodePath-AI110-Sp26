class FoodItem:
    def __init__(self, name: str, price: float, category: str, popularity_rating: float):
        self.name = name
        self.price = price
        self.category = category
        self.popularity_rating = popularity_rating


class Menu:
    def __init__(self):
        self.items: list[FoodItem] = []

    def filter_by_category(self, category: str) -> list[FoodItem]:
        return [item for item in self.items if item.category == category]


class Transaction:
    def __init__(self):
        self.items: list[FoodItem] = []

    def compute_total(self) -> float:
        return sum(item.price for item in self.items)


class Customer:
    def __init__(self, name: str):
        self.name = name
        self.purchase_history: list[Transaction] = []
