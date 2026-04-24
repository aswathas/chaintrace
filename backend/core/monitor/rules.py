"""In-memory rule matcher for alert triggering."""
from dataclasses import dataclass
from typing import Callable
from backend.models.alert import AlertEvent, AlertRule


@dataclass
class AlertRuleMatcher:
    """Match AlertEvents against configured rules."""

    rules: list[AlertRule] = None

    def __post_init__(self):
        if self.rules is None:
            self.rules = []

    def matches(self, event: AlertEvent) -> list[AlertRule]:
        """Return all rules triggered by this event."""
        triggered = []
        for rule in self.rules:
            if self._rule_matches(rule, event):
                triggered.append(rule)
        return triggered

    def _rule_matches(self, rule: AlertRule, event: AlertEvent) -> bool:
        """Check if rule applies to event."""
        # Address match
        if rule.address and rule.address.lower() != event.address.lower():
            return False

        # Value threshold
        if rule.min_value_usd and event.value_usd < rule.min_value_usd:
            return False

        # Label-based (would query label service)
        if rule.label_filter:
            # Placeholder: check if event.address has label matching rule.label_filter
            pass

        return True

    def add_rule(self, rule: AlertRule) -> None:
        """Add a rule dynamically."""
        self.rules.append(rule)

    def remove_rule(self, rule_id: str) -> None:
        """Remove rule by ID."""
        self.rules = [r for r in self.rules if r.id != rule_id]
