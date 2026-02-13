from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_classify_endpoint():
    """Test POST /api/v1/email/classify returns valid response."""
    response = client.post(
        "/api/v1/email/classify",
        json={
            "from_address": "kunde@firma.de",
            "from_name": "Max Mustermann",
            "subject": "Angebot AI-Beratung",
            "body_preview": "Sehr geehrter Herr Müller, ...",
            "has_attachments": False,
            "importance": "normal",
            "account": "business",
            "message_id": "test-msg-001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "priority" in data
    assert "actions" in data
    assert "confidence" in data
    assert "tier_used" in data
    assert "reasoning" in data
    assert data["dry_run"] is False
    # Verify email echo fields
    assert "email" in data
    assert data["email"]["from_address"] == "kunde@firma.de"
    assert data["email"]["from_name"] == "Max Mustermann"
    assert data["email"]["subject"] == "Angebot AI-Beratung"
    assert data["email"]["account"] == "business"


def test_test_classify_endpoint():
    """Test POST /api/v1/email/test-classify sets dry_run=True."""
    response = client.post(
        "/api/v1/email/test-classify",
        json={
            "from_address": "test@test.de",
            "subject": "Test Rechnung",
            "body_preview": "Anbei die Rechnung",
            "has_attachments": True,
            "importance": "normal",
            "account": "business",
            "message_id": "test-123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True


def test_rules_endpoint():
    """Test GET /api/v1/email/rules returns rules list."""
    response = client.get("/api/v1/email/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert "total" in data
    assert "source" in data
    assert data["total"] > 0
    assert data["source"] == "config_file"

    # Check rule structure
    first_rule = data["rules"][0]
    assert "name" in first_rule
    assert "category" in first_rule
    assert "priority" in first_rule
    assert "actions" in first_rule
    assert "conditions" in first_rule


def test_classify_invoice():
    """Test that an invoice email is classified correctly."""
    response = client.post(
        "/api/v1/email/classify",
        json={
            "from_address": "billing@hetzner.com",
            "subject": "Ihre Rechnung Nr. 12345",
            "body_preview": "Ihre monatliche Rechnung",
            "has_attachments": True,
            "importance": "normal",
            "account": "business",
            "message_id": "test-invoice-001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "invoice"
    assert data["priority"] == "medium"


def test_classify_server_alert():
    """Test that a server alert is classified correctly."""
    response = client.post(
        "/api/v1/email/classify",
        json={
            "from_address": "root@proxmox.local",
            "subject": "Backup Report",
            "body_preview": "Backup completed successfully",
            "has_attachments": False,
            "importance": "high",
            "account": "business",
            "message_id": "test-alert-001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "server_alert"
    assert data["priority"] == "high"


def test_classify_minimal_fields():
    """Test that classification works with minimal input (all fields have defaults)."""
    response = client.post(
        "/api/v1/email/classify",
        json={
            "subject": "Test",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data


def test_classify_empty_received_at():
    """Test that empty string received_at is handled gracefully."""
    response = client.post(
        "/api/v1/email/classify",
        json={
            "from_address": "test@test.de",
            "subject": "Test",
            "received_at": "",
            "account": "business",
            "message_id": "test-123",
        },
    )
    assert response.status_code == 200


def test_classify_invalid_body():
    """Test validation error with completely invalid input."""
    response = client.post(
        "/api/v1/email/classify",
        json="not a json object",
    )
    assert response.status_code == 422


def test_health_still_works():
    """Ensure health endpoint still works after adding email router."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
