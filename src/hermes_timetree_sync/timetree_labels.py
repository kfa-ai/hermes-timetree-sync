from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_LABEL_POLICY_PATH = Path("timetree-labels.yaml")
LABEL_POLICY_ENV_VAR = "TIMETREE_LABEL_POLICY_FILE"


class TimeTreeLabelPolicyError(ValueError):
    """Raised when a label policy file is invalid."""


@dataclass(frozen=True)
class LabelRule:
    category: str
    label_id: int
    terms: tuple[str, ...] = ()
    colour: str | None = None


@dataclass(frozen=True)
class LabelPolicy:
    rules: tuple[LabelRule, ...] = ()

    @classmethod
    def from_file(cls, path: str | Path) -> LabelPolicy:
        policy_path = Path(path).expanduser()
        try:
            raw = yaml.safe_load(policy_path.read_text())
        except OSError as exc:
            raise TimeTreeLabelPolicyError(f"could not read label policy file: {policy_path}") from exc
        return cls.from_mapping(raw, source=str(policy_path))

    @classmethod
    def from_mapping(cls, raw: Any, *, source: str = "label policy") -> LabelPolicy:
        if raw is None:
            return cls()
        if not isinstance(raw, Mapping):
            raise TimeTreeLabelPolicyError(f"{source} must be a YAML mapping")

        raw_rules = raw.get("rules", [])
        if not isinstance(raw_rules, list):
            raise TimeTreeLabelPolicyError(f"{source} field 'rules' must be a list")

        rules: list[LabelRule] = []
        for index, raw_rule in enumerate(raw_rules, start=1):
            if not isinstance(raw_rule, Mapping):
                raise TimeTreeLabelPolicyError(f"{source} rule {index} must be a mapping")

            category = raw_rule.get("category")
            label_id = raw_rule.get("label_id")
            terms = raw_rule.get("terms", [])
            colour = raw_rule.get("colour")

            if not isinstance(category, str) or not category.strip():
                raise TimeTreeLabelPolicyError(f"{source} rule {index} requires a category")
            if not isinstance(label_id, int):
                raise TimeTreeLabelPolicyError(f"{source} rule {index} requires integer label_id")
            if terms is None:
                terms = []
            if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
                raise TimeTreeLabelPolicyError(f"{source} rule {index} terms must be a list of strings")
            if colour is not None and not isinstance(colour, str):
                raise TimeTreeLabelPolicyError(f"{source} rule {index} colour must be a string")

            rules.append(
                LabelRule(
                    category=normalise_category(category),
                    label_id=label_id,
                    terms=tuple(term.lower() for term in terms if term.strip()),
                    colour=colour,
                )
            )

        return cls(rules=tuple(rules))

    def label_id_for_category(self, category: str) -> int:
        normalised = normalise_category(category)
        for rule in self.rules:
            if rule.category == normalised:
                return rule.label_id
        known = ", ".join(rule.category for rule in self.rules) or "<none configured>"
        raise TimeTreeLabelPolicyError(
            f"unknown TimeTree category {category!r}; expected one of: {known}"
        )

    def infer_category(self, *, title: str, note: str | None = None) -> str | None:
        haystack = f"{title}\n{note or ''}".lower()
        for rule in self.rules:
            if any(term in haystack for term in rule.terms):
                return rule.category
        return None

    def resolve_label_id(
        self,
        *,
        category: str | None = None,
        title: str = "",
        note: str | None = None,
        default_label_id: int | None = None,
    ) -> int | None:
        if category:
            return self.label_id_for_category(category)
        inferred = self.infer_category(title=title, note=note)
        if inferred:
            return self.label_id_for_category(inferred)
        return default_label_id


def normalise_category(category: str) -> str:
    return category.strip().lower().replace("_", "-").replace(" ", "-")


def load_label_policy(path: str | Path | None = None) -> LabelPolicy:
    policy_path = path or os.getenv(LABEL_POLICY_ENV_VAR) or DEFAULT_LABEL_POLICY_PATH
    expanded = Path(policy_path).expanduser()
    if not expanded.exists():
        return LabelPolicy()
    return LabelPolicy.from_file(expanded)


def apply_label_policy(
    payload: Mapping[str, Any],
    *,
    category: str | None = None,
    default_label_id: int | None = None,
    policy: LabelPolicy | None = None,
) -> dict[str, Any]:
    """Return an event payload with label_id resolved from a YAML label policy.

    Explicit ``category`` wins. Without a category, we infer from the payload
    title/note using configured terms. If no policy/rule matches, we preserve an
    existing label_id or use ``default_label_id`` when provided.
    """

    active_policy = policy or load_label_policy()
    resolved = active_policy.resolve_label_id(
        category=category,
        title=str(payload.get("title") or ""),
        note=str(payload.get("note") or "") if payload.get("note") is not None else None,
        default_label_id=int(payload["label_id"])
        if "label_id" in payload and payload["label_id"] is not None
        else default_label_id,
    )
    result = dict(payload)
    if resolved is not None:
        result["label_id"] = resolved
    return result
