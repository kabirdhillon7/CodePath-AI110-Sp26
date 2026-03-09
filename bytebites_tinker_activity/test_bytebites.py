import pytest
from models import FoodItem, Menu, Transaction, Customer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def burger():
    return FoodItem("Spicy Burger", 9.99, "Burgers", 4.5)

@pytest.fixture
def soda():
    return FoodItem("Large Soda", 2.49, "Drinks", 3.8)

@pytest.fixture
def juice():
    return FoodItem("Orange Juice", 3.99, "Drinks", 4.1)

@pytest.fixture
def brownie():
    return FoodItem("Chocolate Brownie", 4.50, "Desserts", 4.9)

@pytest.fixture
def menu(burger, soda, juice, brownie):
    m = Menu()
    for item in [burger, soda, juice, brownie]:
        m.add_item(item)
    return m


# ---------------------------------------------------------------------------
# FoodItem
# ---------------------------------------------------------------------------

class TestFoodItem:
    def test_food_item_attributes(self, burger):
        assert burger.name == "Spicy Burger"
        assert burger.price == 9.99
        assert burger.category == "Burgers"
        assert burger.popularity_rating == 4.5


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

class TestMenu:
    def test_add_item(self, burger, soda):
        m = Menu()
        m.add_item(burger)
        m.add_item(soda)
        assert len(m.items) == 2

    def test_filter_by_category_match(self, menu):
        drinks = menu.filter_by_category("Drinks")
        assert len(drinks) == 2
        assert all(item.category == "Drinks" for item in drinks)

    def test_filter_by_category_no_match(self, menu):
        result = menu.filter_by_category("Sushi")
        assert result == []

    def test_filter_by_category_case_insensitive(self, menu):
        # "drinks" (lowercase) should match items with category "Drinks"
        result = menu.filter_by_category("drinks")
        assert len(result) == 2

    def test_sort_by_price_ascending(self, menu):
        sorted_items = menu.sort_by_price(ascending=True)
        prices = [item.price for item in sorted_items]
        assert prices == sorted(prices)

    def test_sort_by_price_descending(self, menu):
        sorted_items = menu.sort_by_price(ascending=False)
        prices = [item.price for item in sorted_items]
        assert prices == sorted(prices, reverse=True)

    def test_sort_by_popularity_descending(self, menu):
        # default is descending (highest rated first)
        sorted_items = menu.sort_by_popularity()
        ratings = [item.popularity_rating for item in sorted_items]
        assert ratings == sorted(ratings, reverse=True)

    def test_sort_by_popularity_ascending(self, menu):
        sorted_items = menu.sort_by_popularity(ascending=True)
        ratings = [item.popularity_rating for item in sorted_items]
        assert ratings == sorted(ratings)


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------

class TestTransaction:
    def test_add_item(self, burger, soda):
        t = Transaction()
        t.add_item(burger)
        t.add_item(soda)
        assert burger in t.items
        assert soda in t.items

    def test_get_item_count(self, burger, soda, juice):
        t = Transaction()
        t.add_item(burger)
        t.add_item(soda)
        t.add_item(juice)
        assert t.get_item_count() == 3

    def test_compute_total(self, burger, soda):
        t = Transaction()
        t.add_item(burger)
        t.add_item(soda)
        assert t.compute_total() == pytest.approx(burger.price + soda.price)

    def test_compute_total_empty(self):
        t = Transaction()
        assert t.compute_total() == 0.0


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class TestCustomer:
    def test_customer_name(self):
        c = Customer("Alice")
        assert c.name == "Alice"

    def test_add_transaction(self, burger):
        c = Customer("Alice")
        t = Transaction()
        t.add_item(burger)
        c.add_transaction(t)
        assert t in c.purchase_history

    def test_get_total_spent(self, burger, soda, brownie):
        c = Customer("Alice")

        t1 = Transaction()
        t1.add_item(burger)
        t1.add_item(soda)

        t2 = Transaction()
        t2.add_item(brownie)

        c.add_transaction(t1)
        c.add_transaction(t2)

        expected = burger.price + soda.price + brownie.price
        assert c.get_total_spent() == pytest.approx(expected)

    def test_is_verified_false_no_history(self):
        c = Customer("Bob")
        assert c.is_verified() is False

    def test_is_verified_true_with_history(self, soda):
        c = Customer("Bob")
        t = Transaction()
        t.add_item(soda)
        c.add_transaction(t)
        assert c.is_verified() is True


# ---------------------------------------------------------------------------
# Edge Cases — Transaction
# ---------------------------------------------------------------------------

class TestTransactionEdgeCases:
    def test_compute_total_single_item(self, burger):
        t = Transaction()
        t.add_item(burger)
        assert t.compute_total() == pytest.approx(burger.price)

    def test_compute_total_many_items(self, burger, soda, juice, brownie):
        t = Transaction()
        for item in [burger, soda, juice, brownie]:
            t.add_item(item)
        expected = burger.price + soda.price + juice.price + brownie.price
        assert t.compute_total() == pytest.approx(expected)

    def test_compute_total_free_item(self, soda):
        free_item = FoodItem("Water Cup", 0.0, "Drinks", 3.0)
        t = Transaction()
        t.add_item(soda)
        t.add_item(free_item)
        assert t.compute_total() == pytest.approx(soda.price)

    def test_get_item_count_empty(self):
        t = Transaction()
        assert t.get_item_count() == 0

    def test_get_item_count_single(self, burger):
        t = Transaction()
        t.add_item(burger)
        assert t.get_item_count() == 1


# ---------------------------------------------------------------------------
# Edge Cases — Menu
# ---------------------------------------------------------------------------

class TestMenuEdgeCases:
    def test_filter_empty_menu(self):
        m = Menu()
        assert m.filter_by_category("Drinks") == []

    def test_filter_single_match(self, burger):
        m = Menu()
        m.add_item(burger)
        result = m.filter_by_category("Burgers")
        assert len(result) == 1
        assert result[0] is burger

    def test_filter_all_caps_category(self, soda, juice):
        m = Menu()
        m.add_item(soda)
        m.add_item(juice)
        result = m.filter_by_category("DRINKS")
        assert len(result) == 2

    def test_sort_price_empty_menu(self):
        m = Menu()
        assert m.sort_by_price() == []

    def test_sort_popularity_empty_menu(self):
        m = Menu()
        assert m.sort_by_popularity() == []

    def test_sort_price_single_item(self, burger):
        m = Menu()
        m.add_item(burger)
        result = m.sort_by_price()
        assert result == [burger]


# ---------------------------------------------------------------------------
# Edge Cases — Customer
# ---------------------------------------------------------------------------

class TestCustomerEdgeCases:
    def test_get_total_spent_no_transactions(self):
        c = Customer("Alice")
        assert c.get_total_spent() == 0.0

    def test_get_total_spent_single_transaction(self, burger, soda):
        c = Customer("Alice")
        t = Transaction()
        t.add_item(burger)
        t.add_item(soda)
        c.add_transaction(t)
        assert c.get_total_spent() == pytest.approx(burger.price + soda.price)

    def test_get_total_spent_empty_transaction(self):
        c = Customer("Alice")
        t = Transaction()  # no items
        c.add_transaction(t)
        assert c.get_total_spent() == 0.0
