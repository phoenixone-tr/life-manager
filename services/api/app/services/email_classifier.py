import json
import logging
from pathlib import Path

from app.models.email import (
    EmailAction,
    EmailCategory,
    EmailClassifyRequest,
    EmailClassifyResponse,
    EmailPriority,
    EmailRule,
)

logger = logging.getLogger(__name__)


class EmailClassifier:
    """Tier 1: Rule-based email classifier using configurable rules."""

    def __init__(self, rules_path: str | Path | None = None):
        if rules_path is None:
            # Default: look for config relative to project root
            rules_path = Path("/app/config/email_rules.json")
            if not rules_path.exists():
                # Fallback for local development
                rules_path = (
                    Path(__file__).parent.parent.parent.parent.parent
                    / "config"
                    / "email_rules.json"
                )
        self.rules_path = Path(rules_path)
        self._rules: list[dict] | None = None

    def _load_rules(self) -> list[dict]:
        """Load rules from config file. Reloads on every call for hot-reload."""
        try:
            with open(self.rules_path) as f:
                data = json.load(f)
            return data.get("rules", [])
        except FileNotFoundError:
            logger.error("Rules file not found: %s", self.rules_path)
            return []
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in rules file: %s", e)
            return []

    def get_rules(self) -> list[EmailRule]:
        """Return all rules as Pydantic models."""
        raw_rules = self._load_rules()
        result = []
        for rule in raw_rules:
            result.append(
                EmailRule(
                    name=rule["name"],
                    category=rule["category"],
                    priority=rule["priority"],
                    actions=rule["actions"],
                    conditions=rule["conditions"],
                    description=rule.get("description", ""),
                )
            )
        return result

    def classify(
        self, email: EmailClassifyRequest, dry_run: bool = False
    ) -> EmailClassifyResponse:
        """Classify an email using Tier 1 rules."""
        rules = self._load_rules()

        for rule in rules:
            match, reasoning = self._evaluate_rule(rule, email)
            if match:
                return EmailClassifyResponse(
                    category=EmailCategory(rule["category"]),
                    priority=EmailPriority(rule["priority"]),
                    actions=[EmailAction(a) for a in rule["actions"]],
                    confidence=0.85,
                    tier_used=1,
                    reasoning=reasoning,
                    dry_run=dry_run,
                )

        # No rule matched → uncategorized
        return EmailClassifyResponse(
            category=EmailCategory.UNCATEGORIZED,
            priority=EmailPriority.MEDIUM,
            actions=[EmailAction.NOTIFY_TELEGRAM],
            confidence=0.5,
            tier_used=1,
            reasoning="No classification rule matched",
            dry_run=dry_run,
        )

    def _evaluate_rule(
        self, rule: dict, email: EmailClassifyRequest
    ) -> tuple[bool, str]:
        """Evaluate a single rule against an email. Returns (matched, reasoning)."""
        conditions = rule.get("conditions", {})
        match_type = conditions.get("match_type", "any")
        sub_rules = conditions.get("rules", [])

        if not sub_rules:
            return False, ""

        results = []
        matched_reasons = []

        for sub_rule in sub_rules:
            matched, reason = self._evaluate_condition(sub_rule, email)
            results.append(matched)
            if matched:
                matched_reasons.append(reason)

        if match_type == "all":
            overall_match = all(results)
        else:  # "any"
            overall_match = any(results)

        if overall_match:
            reasoning = f"Rule '{rule['name']}': {'; '.join(matched_reasons)}"
            return True, reasoning

        return False, ""

    def _evaluate_condition(
        self, condition: dict, email: EmailClassifyRequest
    ) -> tuple[bool, str]:
        """Evaluate a single condition against an email field."""
        field = condition.get("field", "")
        operator = condition.get("operator", "")
        values = condition.get("values", [])

        field_value = self._get_field_value(field, email)

        if operator == "contains_any":
            field_lower = field_value.lower()
            for value in values:
                if value.lower() in field_lower:
                    return True, f"{field} contains '{value}'"
            return False, ""

        elif operator == "not_contains_any":
            field_lower = field_value.lower()
            for value in values:
                if value.lower() in field_lower:
                    return False, ""
            return True, f"{field} does not contain blocked patterns"

        elif operator == "equals":
            for value in values:
                if field_value.lower() == value.lower():
                    return True, f"{field} equals '{value}'"
            return False, ""

        elif operator == "not_equals":
            for value in values:
                if field_value.lower() == value.lower():
                    return False, ""
            return True, f"{field} is not in excluded values"

        else:
            logger.warning("Unknown operator: %s", operator)
            return False, ""

    def _get_field_value(self, field: str, email: EmailClassifyRequest) -> str:
        """Extract a field value from the email as a string."""
        field_map = {
            "from_address": email.from_address,
            "from_name": email.from_name,
            "subject": email.subject,
            "body_preview": email.body_preview,
            "account": email.account.value,
            "importance": email.importance.value,
        }
        return field_map.get(field, "")
