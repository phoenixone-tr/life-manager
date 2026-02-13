from pathlib import Path

from app.models.email import EmailAccount, EmailClassifyRequest, EmailImportance
from app.services.email_classifier import EmailClassifier

# Use the actual config file from the project
CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "email_rules.json"


def _make_email(**kwargs) -> EmailClassifyRequest:
    """Helper to create test email requests with sensible defaults."""
    defaults = {
        "from_address": "someone@example.com",
        "from_name": "Someone",
        "subject": "Test Email",
        "body_preview": "This is a test email.",
        "has_attachments": False,
        "importance": EmailImportance.NORMAL,
        "account": EmailAccount.BUSINESS,
        "message_id": "test-msg-001",
    }
    defaults.update(kwargs)
    return EmailClassifyRequest(**defaults)


def get_classifier() -> EmailClassifier:
    return EmailClassifier(rules_path=CONFIG_PATH)


class TestServerAlerts:
    def test_proxmox_alert(self):
        c = get_classifier()
        email = _make_email(
            from_address="noreply@proxmox.local",
            subject="Backup completed",
        )
        result = c.classify(email)
        assert result.category.value == "server_alert"
        assert result.priority.value == "high"

    def test_subject_alert_keyword(self):
        c = get_classifier()
        email = _make_email(
            from_address="admin@myserver.de",
            subject="ALERT: Disk space low on VM 211",
        )
        result = c.classify(email)
        assert result.category.value == "server_alert"

    def test_fail2ban_notification(self):
        c = get_classifier()
        email = _make_email(
            from_address="fail2ban@server.local",
            subject="[Fail2Ban] SSH banned IP",
        )
        result = c.classify(email)
        assert result.category.value == "server_alert"


class TestInvoice:
    def test_rechnung_subject(self):
        c = get_classifier()
        email = _make_email(
            from_address="billing@hetzner.com",
            subject="Ihre Rechnung Nr. 12345",
            has_attachments=True,
        )
        result = c.classify(email)
        assert result.category.value == "invoice"
        assert result.priority.value == "medium"

    def test_invoice_english(self):
        c = get_classifier()
        email = _make_email(
            from_address="noreply@aws.amazon.com",
            subject="Your AWS Invoice is available",
        )
        result = c.classify(email)
        assert result.category.value == "invoice"

    def test_payment_body(self):
        c = get_classifier()
        email = _make_email(
            from_address="service@ionos.de",
            subject="Ihre Bestellung",
            body_preview="Ihre Rechnung im Anhang finden Sie hier.",
        )
        result = c.classify(email)
        assert result.category.value == "invoice"


class TestNewsletter:
    def test_newsletter_from(self):
        c = get_classifier()
        email = _make_email(
            from_address="newsletter@techcrunch.com",
            subject="Daily Tech Roundup",
        )
        result = c.classify(email)
        assert result.category.value == "newsletter"
        assert result.priority.value == "low"
        assert "skip" in [a.value for a in result.actions]

    def test_noreply_marketing(self):
        c = get_classifier()
        email = _make_email(
            from_address="noreply@shop.example.com",
            subject="Unsere Angebote diese Woche",
        )
        result = c.classify(email)
        assert result.category.value == "newsletter"

    def test_unsubscribe_subject(self):
        c = get_classifier()
        email = _make_email(
            from_address="info@company.de",
            subject="Weekly Newsletter - Unsubscribe anytime",
        )
        result = c.classify(email)
        assert result.category.value == "newsletter"


class TestSpam:
    def test_lottery_spam(self):
        c = get_classifier()
        email = _make_email(
            from_address="winner@lottery.com",
            subject="Congratulations! You Won $1,000,000",
        )
        result = c.classify(email)
        assert result.category.value == "spam_suspect"
        assert result.priority.value == "low"

    def test_phishing_body(self):
        c = get_classifier()
        email = _make_email(
            from_address="security@fakepaypal.com",
            subject="Important Notice",
            body_preview="Click here to claim your refund immediately",
        )
        result = c.classify(email)
        assert result.category.value == "spam_suspect"


class TestClientInquiry:
    def test_business_external_sender(self):
        c = get_classifier()
        email = _make_email(
            from_address="kunde@firma.de",
            from_name="Max Mustermann",
            subject="Anfrage: AI-Beratung",
            account=EmailAccount.BUSINESS,
        )
        result = c.classify(email)
        assert result.category.value == "client_inquiry"
        assert result.priority.value == "high"

    def test_business_noreply_is_not_client(self):
        """noreply@ on business should match newsletter, not client_inquiry."""
        c = get_classifier()
        email = _make_email(
            from_address="noreply@service.com",
            subject="Your order confirmation",
            account=EmailAccount.BUSINESS,
        )
        result = c.classify(email)
        assert result.category.value == "newsletter"


class TestPersonal:
    def test_family_personal_email(self):
        c = get_classifier()
        email = _make_email(
            from_address="freund@gmail.com",
            from_name="Ein Freund",
            subject="Treffen am Wochenende?",
            account=EmailAccount.FAMILY,
        )
        result = c.classify(email)
        assert result.category.value == "personal"
        assert result.priority.value == "medium"

    def test_family_noreply_is_newsletter(self):
        c = get_classifier()
        email = _make_email(
            from_address="noreply@spotify.com",
            subject="Your weekly playlist",
            account=EmailAccount.FAMILY,
        )
        result = c.classify(email)
        assert result.category.value == "newsletter"


class TestEdgeCases:
    def test_empty_subject(self):
        c = get_classifier()
        email = _make_email(
            from_address="someone@company.de",
            subject="",
            account=EmailAccount.BUSINESS,
        )
        result = c.classify(email)
        # Should still classify (as client_inquiry since business + real sender)
        assert result.category is not None

    def test_unknown_sender_family(self):
        c = get_classifier()
        email = _make_email(
            from_address="random123@unknown.org",
            subject="Hello",
            account=EmailAccount.FAMILY,
        )
        result = c.classify(email)
        assert result.category.value == "personal"

    def test_dry_run_flag(self):
        c = get_classifier()
        email = _make_email(
            from_address="test@test.de",
            subject="Test",
            account=EmailAccount.BUSINESS,
        )
        result = c.classify(email, dry_run=True)
        assert result.dry_run is True

    def test_confidence_is_valid(self):
        c = get_classifier()
        email = _make_email(
            from_address="test@test.de",
            subject="Test",
        )
        result = c.classify(email)
        assert 0.0 <= result.confidence <= 1.0

    def test_tier_used_is_one(self):
        c = get_classifier()
        email = _make_email(
            from_address="test@test.de",
            subject="Test",
        )
        result = c.classify(email)
        assert result.tier_used == 1

    def test_response_includes_email_summary(self):
        """Verify the response echoes back the input email fields."""
        c = get_classifier()
        email = _make_email(
            from_address="kunde@firma.de",
            from_name="Max Mustermann",
            subject="Anfrage AI",
            body_preview="Sehr geehrter Herr Müller",
            account=EmailAccount.BUSINESS,
        )
        result = c.classify(email)
        assert result.email.from_address == "kunde@firma.de"
        assert result.email.from_name == "Max Mustermann"
        assert result.email.subject == "Anfrage AI"
        assert result.email.body_preview == "Sehr geehrter Herr Müller"
        assert result.email.account == "business"
