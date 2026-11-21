"""Alert email: rendering and delivery through the Resend API."""

import os
from datetime import date
from html import escape
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from monitor import NewFailure, PriceChange, Recovered

FONT = "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;"
TEXT = "#1c1917"
SECONDARY = "#57534e"
MUTED = "#a8a29e"
BACKGROUND = "#fafaf9"
BORDER = "#e7e5e4"
DROP = "#059669"
RISE = "#dc2626"


def send(subject: str, html: str) -> None:
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
        json={
            "from": "Price Tracker <onboarding@resend.dev>",
            "to": [os.environ["EMAIL_TO"]],
            "subject": subject,
            "html": html,
        },
        timeout=30,
    )
    response.raise_for_status()


def render_alert(
    changes: "list[PriceChange]", failures: "list[NewFailure]", recoveries: "list[Recovered]"
) -> tuple[str, str]:
    """Return (subject, html) for one email covering price changes and URLs that started
    failing or work again."""
    drops = sum(1 for c in changes if c.price < c.previous_price)
    rises = len(changes) - drops
    parts = []
    if drops:
        parts.append(f"📉 {drops} price drop{'s' if drops != 1 else ''}")
    if rises:
        parts.append(f"📈 {rises} price increase{'s' if rises != 1 else ''}")
    if failures:
        parts.append(f"⚠️ {len(failures)} URL{'s' if len(failures) != 1 else ''} failing")
    if recoveries:
        parts.append(f"✅ {len(recoveries)} URL{'s' if len(recoveries) != 1 else ''} working again")
    summary = " · ".join(parts)
    accent = DROP if drops or not (rises or failures) else RISE

    rows = "".join(_change_card(c) for c in changes)
    if failures:
        rows += _failures_card(failures)
    if recoveries:
        rows += _recoveries_card(recoveries)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Price Alert</title>
</head>
<body style="margin: 0; padding: 0; background-color: {BACKGROUND}; {FONT}">
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {BACKGROUND};">
<tr><td align="center" style="padding: 24px 16px;">
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 480px;">
<tr><td style="padding-bottom: 28px;">
  <div style="width: 40px; height: 4px; background-color: {accent}; border-radius: 2px; margin-bottom: 16px;"></div>
  <h1 style="margin: 0; {FONT} font-size: 28px; font-weight: 700; color: {TEXT}; letter-spacing: -0.5px;">Price Alert</h1>
  <div style="padding-top: 8px; {FONT} font-size: 16px; color: {MUTED};">{date.today():%b %d, %Y} · {summary}</div>
</td></tr>
{rows}
<tr><td style="border-top: 1px solid {BORDER}; padding-top: 16px; {FONT} font-size: 12px; color: {MUTED};">
  Automated monitoring · checked daily
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
    return summary, html


def _change_card(change: "PriceChange") -> str:
    is_drop = change.price < change.previous_price
    color = DROP if is_drop else RISE
    badge_background = "#ecfdf5" if is_drop else "#fef2f2"
    difference = abs(change.price - change.previous_price)
    percent = difference / change.previous_price * 100
    difference_text = f"You save {difference:.2f}€" if is_drop else f"+{difference:.2f}€"

    details = ""
    if change.original_price:
        details += _detail(f"List price: {change.original_price:.2f}€")
    lowest = change.all_time_lowest
    if lowest and change.price <= lowest["price"]:
        details += f"""
  <div style="margin-top: 12px; padding: 10px 14px; background-color: #fef3c7; border-radius: 8px; {FONT} font-size: 14px; font-weight: 600; color: #92400e;">Lowest price ever recorded</div>"""
    elif lowest:
        details += _detail(
            f"Historical low: <strong>{lowest['price']:.2f}€</strong> on {lowest['date']}"
            f" at {escape(lowest['store'])}"
        )
    if len(change.in_stock_prices) > 1:
        others = " · ".join(
            f"{escape(store)} {price:.2f}€"
            for store, price in sorted(change.in_stock_prices.items(), key=lambda item: item[1])
        )
        details += _detail(f"In stock: {others}")

    return f"""
<tr><td style="padding: 20px; background-color: #ffffff; border-radius: 12px;">
  <span style="display: inline-block; background-color: {badge_background}; padding: 6px 12px; border-radius: 20px; {FONT} font-size: 13px; font-weight: 700; color: {color};">{"↓" if is_drop else "↑"} {percent:.0f}%</span>
  <div style="margin-top: 14px; {FONT} font-size: 11px; font-weight: 600; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.5px;">{escape(change.store)}</div>
  <div style="{FONT} font-size: 18px; font-weight: 500; color: {TEXT}; line-height: 1.4;">{escape(change.name)}</div>
  <div style="margin-top: 16px; {FONT} font-size: 36px; font-weight: 600; color: {TEXT}; letter-spacing: -1px;">{change.price:.2f}<span style="font-size: 18px; font-weight: 500; color: {MUTED}; margin-left: 4px;">€</span></div>
  <div style="padding-top: 6px; {FONT}">
    <span style="font-size: 17px; color: {MUTED}; text-decoration: line-through;">{change.previous_price:.2f}€</span>
    <span style="font-size: 16px; font-weight: 600; color: {color}; margin-left: 10px;">{difference_text}</span>
  </div>{details}
  <div style="margin-top: 16px;">
    <a href="{escape(change.url)}" target="_blank" style="display: inline-block; padding: 12px 20px; {FONT} font-size: 14px; font-weight: 600; color: #ffffff; background-color: {TEXT}; text-decoration: none; border-radius: 8px;">View deal →</a>
  </div>
</td></tr>
<tr><td style="height: 12px;"></td></tr>"""


def _detail(text: str) -> str:
    return f"""
  <div style="margin-top: 12px; {FONT} font-size: 12px; color: {SECONDARY};">{text}</div>"""


def _failures_card(failures: "list[NewFailure]") -> str:
    items = "".join(
        f"""
  <div style="margin-top: 12px; {FONT} font-size: 13px; color: {TEXT};">
    <strong>{escape(f.name)}</strong><br>
    <a href="{escape(f.url)}" style="color: {SECONDARY}; word-break: break-all;">{escape(f.url)}</a><br>
    <span style="color: {RISE}; word-break: break-all;">{escape(f.error)}</span>
  </div>"""
        for f in failures
    )
    return f"""
<tr><td style="padding: 20px; background-color: #ffffff; border-radius: 12px;">
  <div style="{FONT} font-size: 13px; font-weight: 600; color: {SECONDARY}; text-transform: uppercase; letter-spacing: 0.5px;">Could not read these pages</div>{items}
  <div style="margin-top: 12px; {FONT} font-size: 12px; color: {MUTED};">Reported once, when a URL starts failing. Fix or remove it in products.yaml.</div>
</td></tr>
<tr><td style="height: 12px;"></td></tr>"""


def _recoveries_card(recoveries: "list[Recovered]") -> str:
    items = "".join(
        f"""
  <div style="margin-top: 12px; {FONT} font-size: 13px; color: {TEXT};">
    <strong>{escape(r.name)}</strong> · {r.price:.2f}€ ({"in stock" if r.available else "out of stock"})<br>
    <a href="{escape(r.url)}" style="color: {SECONDARY}; word-break: break-all;">{escape(r.url)}</a>
  </div>"""
        for r in recoveries
    )
    return f"""
<tr><td style="padding: 20px; background-color: #ffffff; border-radius: 12px;">
  <div style="{FONT} font-size: 13px; font-weight: 600; color: {DROP}; text-transform: uppercase; letter-spacing: 0.5px;">Working again</div>{items}
</td></tr>
<tr><td style="height: 12px;"></td></tr>"""
