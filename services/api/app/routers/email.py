import logging

from fastapi import APIRouter

from app.models.email import (
    EmailClassifyRequest,
    EmailClassifyResponse,
    EmailRulesResponse,
)
from app.services.email_classifier import EmailClassifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/email", tags=["email"])

classifier = EmailClassifier()


@router.post("/classify", response_model=EmailClassifyResponse)
async def classify_email(email: EmailClassifyRequest):
    """Classify an incoming email using Tier 1 (rule-based) classification."""
    logger.info(
        "Classifying email: from=%s subject='%s' account=%s",
        email.from_address,
        email.subject,
        email.account.value,
    )
    result = classifier.classify(email)
    logger.info(
        "Classification result: category=%s priority=%s actions=%s",
        result.category.value,
        result.priority.value,
        [a.value for a in result.actions],
    )
    return result


@router.post("/test-classify", response_model=EmailClassifyResponse)
async def test_classify_email(email: EmailClassifyRequest):
    """Classify an email in dry-run mode. Logs only, no actions triggered."""
    logger.info("DRY RUN - Classifying email: from=%s subject='%s'", email.from_address, email.subject)
    result = classifier.classify(email, dry_run=True)
    logger.info(
        "DRY RUN - Result: category=%s priority=%s",
        result.category.value,
        result.priority.value,
    )
    return result


@router.get("/rules", response_model=EmailRulesResponse)
async def get_rules():
    """Return the current email classification rules (for debugging/transparency)."""
    rules = classifier.get_rules()
    return EmailRulesResponse(
        rules=rules,
        total=len(rules),
        source="config_file",
    )
