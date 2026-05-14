from __future__ import annotations

import pytest

from hermes_timetree_sync.timetree_labels import (
    LabelPolicy,
    TimeTreeLabelPolicyError,
    apply_label_policy,
    load_label_policy,
)


def sample_policy() -> LabelPolicy:
    return LabelPolicy.from_mapping(
        {
            "rules": [
                {"category": "example-medical", "label_id": 3, "terms": ["doctor", "gp"]},
                {"category": "example-holiday", "label_id": 1, "terms": ["holiday"]},
                {"category": "example-personal", "label_id": 5, "terms": ["day off"]},
            ]
        }
    )


def test_loads_label_policy_from_yaml_file(tmp_path) -> None:
    policy_path = tmp_path / "labels.yaml"
    policy_path.write_text(
        """
rules:
  - category: example-medical
    colour: blue
    label_id: 3
    terms: [doctor, gp]
""".strip()
    )

    policy = load_label_policy(policy_path)

    assert policy.label_id_for_category("example-medical") == 3
    assert policy.infer_category(title="GP appointment") == "example-medical"


@pytest.mark.parametrize(
    ("title", "expected_category", "expected_label_id"),
    [
        ("Doctor appointment", "example-medical", 3),
        ("Public holiday", "example-holiday", 1),
        ("Day off", "example-personal", 5),
    ],
)
def test_infers_categories_from_configured_terms(
    title: str, expected_category: str, expected_label_id: int
) -> None:
    policy = sample_policy()

    assert policy.infer_category(title=title) == expected_category
    assert policy.resolve_label_id(title=title) == expected_label_id


def test_explicit_category_overrides_inference() -> None:
    assert sample_policy().resolve_label_id(category="example-medical", title="Day off") == 3


def test_unknown_category_raises_clear_error() -> None:
    with pytest.raises(TimeTreeLabelPolicyError, match="unknown TimeTree category"):
        sample_policy().label_id_for_category("chores")


def test_missing_policy_file_is_noop() -> None:
    policy = load_label_policy("/definitely/not/a/real/timetree-labels.yaml")

    assert policy.rules == ()
    assert policy.resolve_label_id(title="Doctor") is None


def test_apply_label_policy_preserves_unknown_existing_label() -> None:
    result = apply_label_policy({"title": "Groceries", "label_id": 4}, policy=sample_policy())

    assert result["label_id"] == 4


def test_apply_label_policy_sets_label_id_for_inferred_category() -> None:
    assert apply_label_policy({"title": "GP"}, policy=sample_policy())["label_id"] == 3


def test_apply_label_policy_can_use_explicit_category() -> None:
    result = apply_label_policy({"title": "Day off"}, category="example-personal", policy=sample_policy())

    assert result["label_id"] == 5


def test_invalid_policy_shape_raises_clear_error() -> None:
    with pytest.raises(TimeTreeLabelPolicyError, match="rules"):
        LabelPolicy.from_mapping({"rules": "not-a-list"})
