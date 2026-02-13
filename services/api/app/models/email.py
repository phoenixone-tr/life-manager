from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class EmailAccount(str, Enum):
    BUSINESS = "business"
    FAMILY = "family"


class EmailImportance(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmailCategory(str, Enum):
    SERVER_ALERT = "server_alert"
    INVOICE = "invoice"
    CLIENT_INQUIRY = "client_inquiry"
    NEWSLETTER = "newsletter"
    PERSONAL = "personal"
    SPAM_SUSPECT = "spam_suspect"
    UNCATEGORIZED = "uncategorized"


class EmailAction(str, Enum):
    NOTIFY_TELEGRAM = "notify_telegram"
    SKIP = "skip"


class EmailClassifyRequest(BaseModel):
    from_address: str = Field("", description="Sender email address")
    from_name: str = Field("", description="Sender display name")
    subject: str = Field("", description="Email subject line")
    body_preview: str = Field("", description="First ~255 characters of email body")
    received_at: datetime | None = Field(None, description="When the email was received")
    has_attachments: bool = Field(False, description="Whether email has attachments")
    importance: EmailImportance = Field(
        EmailImportance.NORMAL, description="Email importance flag"
    )
    account: EmailAccount = Field(EmailAccount.BUSINESS, description="Which M365 account received this")
    message_id: str = Field("", description="Microsoft Graph message ID")

    @field_validator("received_at", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class EmailClassifyResponse(BaseModel):
    category: EmailCategory
    priority: EmailPriority
    actions: list[EmailAction]
    confidence: float = Field(..., ge=0.0, le=1.0)
    tier_used: int = Field(1, description="Classification tier (1=rules, 2=LLM)")
    reasoning: str = Field("", description="Why this classification was chosen")
    dry_run: bool = Field(False, description="Whether this was a test run")


class EmailRule(BaseModel):
    name: str
    category: EmailCategory
    priority: EmailPriority
    actions: list[EmailAction]
    conditions: dict
    description: str = ""


class EmailRulesResponse(BaseModel):
    rules: list[EmailRule]
    total: int
    source: str = Field("config_file", description="Where rules are loaded from")
