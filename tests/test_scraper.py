import pytest

from scraper import NoProductData, Offer, parse_offer


def page(script: str) -> str:
    return f"<html><head>{script}</head><body></body></html>"


def json_ld(body: str) -> str:
    return page(f'<script type="application/ld+json">{body}</script>')


def test_json_ld_product_on_sale_has_price_list_price_and_stock():
    html = json_ld("""
        {"@type": "Product", "name": "Essential Socks 10-pack", "sku": "10005071_MP001",
         "offers": {"@type": "Offer", "price": 35.96, "priceCurrency": "EUR",
                    "priceSpecification": {"@type": "UnitPriceSpecification",
                                           "priceType": "https://schema.org/StrikethroughPrice",
                                           "price": 44.95},
                    "availability": "https://schema.org/InStock"}}
    """)
    assert parse_offer(html) == Offer(price=35.96, available=True, original_price=44.95)


def test_json_ld_string_price_and_out_of_stock():
    html = json_ld("""
        {"@type": "Product", "name": "Premium Omega-3", "sku": "6430050004729",
         "offers": {"@type": "Offer", "price": "29.90",
                    "availability": "http://schema.org/OutOfStock"}}
    """)
    assert parse_offer(html) == Offer(price=29.9, available=False, original_price=None)


def test_json_ld_product_inside_a_list_with_offers_list():
    html = json_ld("""
        [{"@type": "BreadcrumbList"},
         {"@type": "Product", "name": "Omega-3",
          "offers": [{"price": "51.99", "availability": "https://schema.org/InStock"}]}]
    """)
    assert parse_offer(html) == Offer(price=51.99, available=True, original_price=None)


def test_fitnesstukku_tracking_view():
    html = page("""<script>
        var view = [{"event":"pageView"},{"event":"productDetail","ecommerce":{"currencyCode":"EUR","detail":{"products":[{"id":"609","name":"Kreatiinimonohydraatti 500 g","price":"8.90","availability":"IN STOCK"}]}}}]
        window.dataTrackingView = [...window.dataTrackingView || [], ...view];
    </script>""")
    assert parse_offer(html) == Offer(price=8.9, available=True, original_price=None)


def test_page_without_product_data_is_an_error():
    html = json_ld('{"@type": "BreadcrumbList"}')
    with pytest.raises(NoProductData):
        parse_offer(html)
