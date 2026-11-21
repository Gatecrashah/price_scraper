from emails import render_alert
from monitor import NewFailure, PriceChange, Recovered

DROP = PriceChange(
    name="Omega-3 <180>",
    store="tokmanni",
    url="https://www.tokmanni.fi/omega-123",
    price=29.9,
    previous_price=31.9,
    original_price=None,
    all_time_lowest={"price": 27.42, "store": "apteekki360", "url": "x", "date": "2026-01-25"},
    in_stock_prices={"apteekki360": 31.9, "tokmanni": 29.9},
)


def test_drop_email_shows_prices_saving_history_and_link():
    subject, html = render_alert([DROP], [], [])

    assert subject == "📉 1 price drop"
    assert "Omega-3 &lt;180&gt;" in html
    assert "29.90" in html
    assert "31.90€" in html
    assert "You save 2.00€" in html
    assert "↓ 6%" in html
    assert "Historical low: <strong>27.42€</strong> on 2026-01-25 at apteekki360" in html
    assert "In stock: tokmanni 29.90€ · apteekki360 31.90€" in html
    assert 'href="https://www.tokmanni.fi/omega-123"' in html
    assert "Lowest price ever recorded" not in html


def test_new_all_time_low_is_highlighted():
    record = PriceChange(
        name="Socks",
        store="bjornborg",
        url="https://www.bjornborg.com/fi/socks/",
        price=31.47,
        previous_price=44.95,
        original_price=44.95,
        all_time_lowest={"price": 35.96, "store": "bjornborg", "url": "x", "date": "2026-02-03"},
        in_stock_prices={"bjornborg": 31.47},
    )

    _, html = render_alert([record], [], [])

    assert "Lowest price ever recorded" in html
    assert "List price: 44.95€" in html
    assert "Historical low" not in html
    assert "In stock:" not in html


def test_failures_are_listed_with_url_and_error():
    failure = NewFailure(
        "Socks", "https://www.bjornborg.com/fi/gone/", "HTTPError: 404 <Not Found>"
    )

    subject, html = render_alert([], [failure], [])

    assert subject == "⚠️ 1 URL failing"
    assert "https://www.bjornborg.com/fi/gone/" in html
    assert "HTTPError: 404 &lt;Not Found&gt;" in html


def test_recoveries_are_listed_with_current_price_and_url():
    recovered = Recovered("Omega-3 <180>", "https://www.ruohonjuuri.fi/products/omega", 37.42, True)

    subject, html = render_alert([], [], [recovered])

    assert subject == "✅ 1 URL working again"
    assert "Working again" in html
    assert "<strong>Omega-3 &lt;180&gt;</strong> · 37.42€ (in stock)" in html
    assert 'href="https://www.ruohonjuuri.fi/products/omega"' in html
    assert "Could not read these pages" not in html
