#!/usr/bin/env python3
"""
Email notification system for Björn Borg product price changes using Resend API
"""

import logging
import os

import requests

from email_templates import EmailTemplates

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self):
        # Get Resend API configuration from environment variables
        self.api_key = os.getenv("RESEND_API_KEY")
        self.email_to = os.getenv("EMAIL_TO")
        self.api_url = "https://api.resend.com/emails"

        if not self.api_key:
            raise ValueError("RESEND_API_KEY environment variable is required")
        if not self.email_to:
            raise ValueError("EMAIL_TO environment variable is required")

    def format_price_change_email(self, price_changes: list[dict]) -> str:
        """Format price changes into HTML email content"""
        return EmailTemplates.create_price_alert_email(price_changes)

    def send_price_alert(self, price_changes: list[dict]) -> bool:
        """Send email notification about price changes using Resend API"""

        if not price_changes:
            logger.info("No price changes to report")
            return True

        try:
            # Determine email subject based on price changes
            drops = sum(
                1
                for change in price_changes
                if change.get("current_price", 0) < change.get("previous_price", 0)
            )
            increases = len(price_changes) - drops

            if drops > 0 and increases == 0:
                subject = f"🧦 📉 {drops} price drop(s)"
            elif increases > 0 and drops == 0:
                subject = f"🧦 📈 {increases} price increase(s)"
            else:
                subject = f"🧦 {len(price_changes)} price change(s)"

            # Create HTML content
            html_content = self.format_price_change_email(price_changes)

            # Prepare the email payload for Resend API
            payload = {
                "from": "Price Tracker <onboarding@resend.dev>",  # Using Resend's default domain
                "to": [self.email_to],
                "subject": subject,
                "html": html_content,
            }

            # Send email via Resend API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                email_id = result.get("id", "unknown")
                logger.info(
                    f"Price alert email sent successfully to {self.email_to} (ID: {email_id})"
                )
                return True
            else:
                logger.error(
                    f"Failed to send email. Status: {response.status_code}, Response: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_scraper_failure_alert(self, error_details: str) -> bool:
        """Send email notification when scraper completely fails"""

        try:
            html_content = EmailTemplates.create_failure_alert_email(error_details)

            payload = {
                "from": "Price Tracker Alert <onboarding@resend.dev>",
                "to": [self.email_to],
                "subject": "🚨 Product Scraper Failure Alert - Action Required",
                "html": html_content,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                email_id = result.get("id", "unknown")
                logger.info(f"Scraper failure alert sent successfully (ID: {email_id})")
                return True
            else:
                logger.error(
                    f"Failed to send failure alert. Status: {response.status_code}, Response: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send scraper failure alert: {e}")
            return False

    def send_analysis_report(self, subject: str, html_content: str) -> bool:
        """Send analysis report email via Resend API"""

        try:
            payload = {
                "from": "Price Analysis <onboarding@resend.dev>",
                "to": [self.email_to],
                "subject": subject,
                "html": html_content,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                email_id = result.get("id", "unknown")
                logger.info(f"Analysis report sent successfully (ID: {email_id})")
                return True
            else:
                logger.error(
                    f"Failed to send report. Status: {response.status_code}, Response: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send analysis report: {e}")
            return False

    def send_test_email(self) -> bool:
        """Send a test email to verify Resend configuration"""

        try:
            html_content = EmailTemplates.create_test_email()

            payload = {
                "from": "Price Tracker <onboarding@resend.dev>",
                "to": [self.email_to],
                "subject": "🧦 Test Email - Björn Borg Price Tracker",
                "html": html_content,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                email_id = result.get("id", "unknown")
                logger.info(f"Test email sent successfully (ID: {email_id})")
                return True
            else:
                logger.error(
                    f"Failed to send test email. Status: {response.status_code}, Response: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False


def main():
    """Test the Resend email sender"""
    import logging

    logging.basicConfig(level=logging.INFO)

    # Create sample price change data for testing
    sample_price_changes = [
        {
            "name": "Essential Socks 10-pack",
            "current_price": 31.47,
            "previous_price": 35.96,
            "original_price": 44.95,
            "purchase_url": "https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/",
        }
    ]

    try:
        email_sender = EmailSender()
        print("Testing Resend email configuration...")

        # Send test email
        if email_sender.send_test_email():
            print("✅ Test email sent successfully!")

            # Send sample price alert
            print("Sending sample price alert...")
            if email_sender.send_price_alert(sample_price_changes):
                print("✅ Sample price alert sent successfully!")
                print("Check your email inbox!")
            else:
                print("❌ Failed to send sample price alert")
        else:
            print("❌ Failed to send test email")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nTo fix this, set the following environment variables:")
        print("export RESEND_API_KEY='your-resend-api-key'")
        print("export EMAIL_TO='<your-email-address>'")


if __name__ == "__main__":
    main()
