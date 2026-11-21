import pytest

from monitor import (
    Failed,
    NewFailure,
    Product,
    Recovered,
    load_products,
    new_history,
    store_name,
    update_product,
)
from scraper import Offer

SOCKS_URL = "https://www.bjornborg.com/fi/socks/"
SOCKS = Product(id="socks", name="Socks", urls=[SOCKS_URL])

A_URL = "https://apteekki360.fi/products/omega"
T_URL = "https://www.tokmanni.fi/omega-123"
OMEGA = Product(id="omega", name="Omega-3", urls=[A_URL, T_URL])


def test_store_name_is_the_site_name_without_www_and_tld():
    assert store_name("https://www.bjornborg.com/fi/socks/") == "bjornborg"
    assert store_name("https://apteekki360.fi/products/omega") == "apteekki360"


def test_first_sighting_records_state_without_reporting_a_change():
    entry = new_history()

    result = update_product(entry, SOCKS, {SOCKS_URL: Offer(44.95, True)}, "2026-01-01")

    assert result == (None, [], [])
    assert entry == {
        "name": "Socks",
        "stores": {
            "bjornborg": {
                "url": SOCKS_URL,
                "price": 44.95,
                "original_price": None,
                "available": True,
                "error": None,
            }
        },
        "current_lowest": {
            "price": 44.95,
            "store": "bjornborg",
            "url": SOCKS_URL,
            "date": "2026-01-01",
        },
        "all_time_lowest": {
            "price": 44.95,
            "store": "bjornborg",
            "url": SOCKS_URL,
            "date": "2026-01-01",
        },
        "price_changes": [
            {
                "date": "2026-01-01",
                "store": "bjornborg",
                "price": 44.95,
                "original_price": None,
                "available": True,
            }
        ],
    }


def test_unchanged_price_adds_nothing_and_a_drop_is_reported_with_the_previous_price():
    entry = new_history()
    update_product(entry, SOCKS, {SOCKS_URL: Offer(44.95, True)}, "2026-01-01")

    same, _, _ = update_product(entry, SOCKS, {SOCKS_URL: Offer(44.95, True)}, "2026-01-02")
    assert same is None
    assert len(entry["price_changes"]) == 1
    assert entry["current_lowest"]["date"] == "2026-01-01"

    change, _, _ = update_product(
        entry, SOCKS, {SOCKS_URL: Offer(35.96, True, 44.95)}, "2026-01-03"
    )
    assert (change.price, change.previous_price, change.original_price) == (35.96, 44.95, 44.95)
    assert change.all_time_lowest["price"] == 44.95
    assert [e["price"] for e in entry["price_changes"]] == [44.95, 35.96]
    assert entry["current_lowest"]["date"] == "2026-01-03"
    assert entry["all_time_lowest"] == {
        "price": 35.96,
        "store": "bjornborg",
        "url": SOCKS_URL,
        "date": "2026-01-03",
    }


def test_price_increase_is_reported_and_keeps_the_all_time_low():
    entry = new_history()
    update_product(entry, SOCKS, {SOCKS_URL: Offer(35.96, True)}, "2026-01-01")

    change, _, _ = update_product(entry, SOCKS, {SOCKS_URL: Offer(44.95, True)}, "2026-01-02")

    assert (change.price, change.previous_price) == (44.95, 35.96)
    assert entry["all_time_lowest"]["price"] == 35.96


def test_lowest_price_ignores_out_of_stock_stores():
    entry = new_history()
    update_product(
        entry, OMEGA, {A_URL: Offer(31.9, True), T_URL: Offer(29.9, False)}, "2026-01-01"
    )
    assert entry["current_lowest"]["store"] == "apteekki360"
    assert entry["current_lowest"]["price"] == 31.9

    change, _, _ = update_product(
        entry, OMEGA, {A_URL: Offer(31.9, True), T_URL: Offer(29.9, True)}, "2026-01-02"
    )

    assert (change.store, change.price, change.previous_price) == ("tokmanni", 29.9, 31.9)
    assert change.url == T_URL
    assert change.in_stock_prices == {"apteekki360": 31.9, "tokmanni": 29.9}
    assert entry["price_changes"][-1] == {
        "date": "2026-01-02",
        "store": "tokmanni",
        "price": 29.9,
        "original_price": None,
        "available": True,
    }


def test_nothing_in_stock_keeps_the_last_known_lowest_and_reports_nothing():
    entry = new_history()
    update_product(entry, SOCKS, {SOCKS_URL: Offer(44.95, True)}, "2026-01-01")

    result = update_product(entry, SOCKS, {SOCKS_URL: Offer(44.95, False)}, "2026-01-02")

    assert result == (None, [], [])
    assert entry["current_lowest"]["price"] == 44.95
    assert entry["price_changes"][-1]["available"] is False


def test_a_failing_url_is_reported_once_keeps_its_price_and_is_reported_when_it_recovers():
    entry = new_history()
    update_product(entry, SOCKS, {SOCKS_URL: Offer(44.95, True)}, "2026-01-01")

    first = update_product(entry, SOCKS, {SOCKS_URL: Failed("404 Not Found")}, "2026-01-02")
    second = update_product(entry, SOCKS, {SOCKS_URL: Failed("404 Not Found")}, "2026-01-03")

    assert first == (None, [NewFailure("Socks", SOCKS_URL, "404 Not Found")], [])
    assert second == (None, [], [])
    assert entry["stores"]["bjornborg"]["price"] == 44.95
    assert entry["stores"]["bjornborg"]["error"] == "404 Not Found"
    assert len(entry["price_changes"]) == 1

    recovered = update_product(entry, SOCKS, {SOCKS_URL: Offer(39.95, True)}, "2026-01-04")
    still_fine = update_product(entry, SOCKS, {SOCKS_URL: Offer(39.95, True)}, "2026-01-05")
    again = update_product(entry, SOCKS, {SOCKS_URL: Failed("timeout")}, "2026-01-06")
    assert recovered[1:] == ([], [Recovered("Socks", SOCKS_URL, 39.95, True)])
    assert still_fine == (None, [], [])
    assert again == (None, [NewFailure("Socks", SOCKS_URL, "timeout")], [])


def test_a_failing_store_does_not_hide_a_change_at_another_store():
    entry = new_history()
    update_product(entry, OMEGA, {A_URL: Offer(31.9, True), T_URL: Offer(33.0, True)}, "2026-01-01")

    change, failures, _ = update_product(
        entry, OMEGA, {A_URL: Failed("429"), T_URL: Offer(33.0, True)}, "2026-01-02"
    )

    assert (change.store, change.price, change.previous_price) == ("tokmanni", 33.0, 31.9)
    assert failures == [NewFailure("Omega-3", A_URL, "429")]


def test_load_products_reads_the_config_and_rejects_duplicate_ids(tmp_path):
    good = tmp_path / "good.yaml"
    good.write_text(f"products:\n  - id: socks\n    name: Socks\n    urls:\n      - {SOCKS_URL}\n")
    assert load_products(good) == [SOCKS]

    duplicated = tmp_path / "dup.yaml"
    duplicated.write_text(
        "products:\n"
        f"  - {{id: socks, name: A, urls: ['{SOCKS_URL}']}}\n"
        f"  - {{id: socks, name: B, urls: ['{A_URL}']}}\n"
    )
    with pytest.raises(ValueError, match="duplicate product ids"):
        load_products(duplicated)
