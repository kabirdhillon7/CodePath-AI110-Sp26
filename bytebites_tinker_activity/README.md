# ByteBites

Backend logic for the ByteBites food ordering app.

## Project Structure

| File | Description |
|------|-------------|
| `models.py` | Four model classes: `FoodItem`, `Menu`, `Transaction`, `Customer` |
| `test_bytebites.py` | pytest test suite (32 tests — happy paths + edge cases) |
| `bytebites_spec.md` | Client feature request and spec |
| `draft_from_copilot.md` | UML class diagram |

## Models

- **`FoodItem`** — represents a menu item with a name, price, category, and popularity rating
- **`Menu`** — holds the full item catalog; supports adding items, filtering by category, and sorting by price or popularity
- **`Transaction`** — groups selected items into a single order and computes the total cost
- **`Customer`** — tracks a customer's name and purchase history; verifies real users

## Running Tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
pytest test_bytebites.py -v
```

## TF Notes
