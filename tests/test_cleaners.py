import etl

def test_safe_float():
    assert etl.safe_float("10.5") == 10.5
    assert etl.safe_float("") is None
    assert etl.safe_float("12x") is None

def test_clean_currency():
    assert etl.clean_currency(" gbp ") == "GBP"
    assert etl.clean_currency("US") is None
    assert etl.clean_currency("U$D") is None

def test_parse_row_success():
    row = {"transaction_id": "t1", "amount": "10", "currency": "gbp"}
    out, err = etl.parse_row(row)
    assert err is None
    assert out == {"transaction_id": "t1", "amount": 10.0, "currency": "GBP"}

def test_parse_row_invalid_amount():
    row = {"transaction_id": "t1", "amount": "12x", "currency": "gbp"}
    out, err = etl.parse_row(row)
    assert out is None
    assert err == "invalid_amount"