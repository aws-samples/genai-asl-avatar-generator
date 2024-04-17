from functions.text2gloss import app


def test_text2glosee():
    stock_price = 75
    input_payload = {"stock_price": stock_price}

    data = app.lambda_handler(input_payload, "")

    assert "id" in data
    assert "price" in data
    assert "type" in data
    assert "timestamp" in data
    assert "qty" in data

    assert data["type"] == "buy"
    assert data["price"] == str(stock_price)
