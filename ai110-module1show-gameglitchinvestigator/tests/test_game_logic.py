from logic_utils import check_guess, parse_guess


# --- check_guess ---

def test_winning_guess():
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"

def test_guess_too_low():
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"

def test_winning_guess_boundary():
    outcome, _ = check_guess(1, 1)
    assert outcome == "Win"

def test_guess_one_above():
    outcome, _ = check_guess(51, 50)
    assert outcome == "Too High"

def test_guess_one_below():
    outcome, _ = check_guess(49, 50)
    assert outcome == "Too Low"


# --- parse_guess ---

def test_parse_guess_none():
    ok, value, err = parse_guess(None)
    assert ok is False
    assert value is None
    assert err == "Enter a guess."

def test_parse_guess_empty_string():
    ok, value, err = parse_guess("")
    assert ok is False
    assert value is None
    assert err == "Enter a guess."

def test_parse_guess_valid_integer():
    ok, value, err = parse_guess("42")
    assert ok is True
    assert value == 42
    assert err is None

def test_parse_guess_decimal_truncates():
    ok, value, err = parse_guess("3.7")
    assert ok is True
    assert value == 3
    assert err is None

def test_parse_guess_non_numeric():
    ok, value, err = parse_guess("abc")
    assert ok is False
    assert value is None
    assert err == "That is not a number."

def test_parse_guess_negative_number():
    ok, value, err = parse_guess("-5")
    assert ok is True
    assert value == -5
    assert err is None
