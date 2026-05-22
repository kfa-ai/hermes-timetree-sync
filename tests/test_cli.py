from __future__ import annotations

import json

from hermes_timetree_sync import cli
from hermes_timetree_sync.cli import build_parser


def test_parser_accepts_doctor_command() -> None:
    args = build_parser().parse_args(["doctor"])
    assert args.command == "doctor"


def test_parser_accepts_list_calendars_command() -> None:
    args = build_parser().parse_args(["list-calendars"])
    assert args.command == "list-calendars"


def test_parser_accepts_create_all_day_command() -> None:
    args = build_parser().parse_args(["create-all-day", "--title", "Day off", "--date", "2026-05-18"])
    assert args.command == "create-all-day"
    assert args.title == "Day off"
    assert args.date == "2026-05-18"


def test_parser_accepts_create_all_day_batch_command() -> None:
    args = build_parser().parse_args(
        [
            "create-all-day-batch",
            "--event",
            "2026-05-18|Day off",
            "--event",
            "2026-05-19|Team planning",
        ]
    )
    assert args.command == "create-all-day-batch"
    assert args.event == ["2026-05-18|Day off", "2026-05-19|Team planning"]


def test_parser_accepts_create_timed_command() -> None:
    args = build_parser().parse_args(
        [
            "create-timed",
            "--title",
            "Lynsey out",
            "--start",
            "2026-05-24T12:00",
            "--end",
            "2026-05-24T18:00",
            "--category",
            "lynsey",
        ]
    )
    assert args.command == "create-timed"
    assert args.title == "Lynsey out"
    assert args.start == "2026-05-24T12:00"
    assert args.end == "2026-05-24T18:00"
    assert args.timezone == "Australia/Melbourne"
    assert args.category == "lynsey"


def test_parser_accepts_sign_in_command() -> None:
    args = build_parser().parse_args(["sign-in"])
    assert args.command == "sign-in"


def test_list_calendars_prints_calendar_json(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_SESSION_COOKIE", "secret-cookie")

    class FakeClient:
        def __init__(self, *, session_cookie: str) -> None:
            assert session_cookie == "secret-cookie"

        def list_calendars(self) -> list[dict[str, str]]:
            return [{"id": "cal_1", "name": "Family"}]

    monkeypatch.setattr(cli, "TimeTreeClient", FakeClient)

    exit_code = cli.main(["list-calendars"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == [{"id": "cal_1", "name": "Family"}]


def test_list_calendars_without_cookie_explains_auth_options(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TIMETREE_SESSION_COOKIE", raising=False)

    exit_code = cli.main(["list-calendars"])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "TIMETREE_SESSION_COOKIE" in err
    assert "sign-in" in err
    assert "non-interactive Hermes use" in err


def test_create_all_day_posts_safe_default_payload(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_SESSION_COOKIE", "secret-cookie")
    monkeypatch.setenv("TIMETREE_CALENDAR_ID", "cal_1")

    class FakeClient:
        def __init__(self, *, session_cookie: str) -> None:
            assert session_cookie == "secret-cookie"

        def get_current_user(self) -> dict[str, str]:
            return {"id": "user_1"}

        def create_event(self, calendar_id: str, payload: dict[str, object]) -> dict[str, object]:
            assert calendar_id == "cal_1"
            assert payload == {
                "title": "Day off",
                "all_day": True,
                "start_at": 1779062400000,
                "start_timezone": "UTC",
                "end_at": 1779062400000,
                "end_timezone": "UTC",
                "category": 1,
                "type": 0,
                "attendees": ["user_1"],
                "alerts": [],
                "recurrences": [],
                "location": "",
                "location_lat": None,
                "location_lon": None,
                "url": None,
                "note": None,
                "attachment": {"virtual_user_attendees": []},
                "files": [],
            }
            return {"event": {"id": "evt_1", "title": "Day off"}}

    monkeypatch.setattr(cli, "TimeTreeClient", FakeClient)

    exit_code = cli.main(["create-all-day", "--title", "Day off", "--date", "2026-05-18"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"event": {"id": "evt_1", "title": "Day off"}}


def test_create_all_day_accepts_numeric_current_user_id(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_SESSION_COOKIE", "secret-cookie")
    monkeypatch.setenv("TIMETREE_CALENDAR_ID", "cal_1")

    class FakeClient:
        def __init__(self, *, session_cookie: str) -> None:
            assert session_cookie == "secret-cookie"

        def get_current_user(self) -> dict[str, object]:
            return {"id": 123456}

        def create_event(self, calendar_id: str, payload: dict[str, object]) -> dict[str, object]:
            assert payload["attendees"] == ["123456"]
            return {"event": {"id": "evt_1", "title": payload["title"]}}

    monkeypatch.setattr(cli, "TimeTreeClient", FakeClient)

    exit_code = cli.main(["create-all-day", "--title", "Day off", "--date", "2026-05-18"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"event": {"id": "evt_1", "title": "Day off"}}


def test_create_all_day_batch_reuses_user_lookup_for_multiple_events(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_SESSION_COOKIE", "secret-cookie")
    monkeypatch.setenv("TIMETREE_CALENDAR_ID", "cal_1")
    created: list[dict[str, object]] = []
    user_lookups = 0

    class FakeClient:
        def __init__(self, *, session_cookie: str) -> None:
            assert session_cookie == "secret-cookie"

        def get_current_user(self) -> dict[str, object]:
            nonlocal user_lookups
            user_lookups += 1
            return {"id": 123456}

        def create_event(self, calendar_id: str, payload: dict[str, object]) -> dict[str, object]:
            assert calendar_id == "cal_1"
            created.append(payload)
            return {"event": {"id": f"evt_{len(created)}", "title": payload["title"]}}

    monkeypatch.setattr(cli, "TimeTreeClient", FakeClient)

    exit_code = cli.main(
        [
            "create-all-day-batch",
            "--event",
            "2026-05-18|Day off",
            "--event",
            "2026-05-19|Team planning",
        ]
    )

    assert exit_code == 0
    assert user_lookups == 1
    assert [event["title"] for event in created] == ["Day off", "Team planning"]
    assert [event["attendees"] for event in created] == [["123456"], ["123456"]]
    assert json.loads(capsys.readouterr().out) == {
        "events": [{"id": "evt_1", "title": "Day off"}, {"id": "evt_2", "title": "Team planning"}]
    }


def test_create_all_day_requires_noninteractive_auth_and_calendar(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TIMETREE_SESSION_COOKIE", raising=False)
    monkeypatch.delenv("TIMETREE_CALENDAR_ID", raising=False)

    exit_code = cli.main(["create-all-day", "--title", "Day off", "--date", "2026-05-18"])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "TIMETREE_SESSION_COOKIE" in err
    assert "TIMETREE_CALENDAR_ID" in err
    assert "TimeTree UI" not in err


def test_sign_in_prints_session_cookie_export(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_EMAIL", "person@example.com")
    monkeypatch.setenv("TIMETREE_PASSWORD", "pw-123")

    def fake_sign_in_with_email(*, email: str, password: str) -> str:
        assert email == "person@example.com"
        assert password == "pw-123"
        return "session-123"

    monkeypatch.setattr(cli, "sign_in_with_email", fake_sign_in_with_email)

    exit_code = cli.main(["sign-in"])

    assert exit_code == 0
    assert capsys.readouterr().out == "TIMETREE_SESSION_COOKIE=session-123\n"


def test_sign_in_requires_email_and_password_without_printing_secret(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_EMAIL", "person@example.com")
    monkeypatch.delenv("TIMETREE_PASSWORD", raising=False)

    exit_code = cli.main(["sign-in"])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "TIMETREE_EMAIL" in err
    assert "TIMETREE_PASSWORD" in err


def test_build_timed_event_payload_uses_local_timezone_and_label_policy(monkeypatch, tmp_path) -> None:
    policy = tmp_path / "labels.yaml"
    policy.write_text("rules:\n  - category: lynsey\n    label_id: 10\n", encoding="utf-8")
    monkeypatch.setenv("TIMETREE_LABEL_POLICY_FILE", str(policy))

    payload = cli.build_timed_event_payload(
        title="Lynsey out",
        start="2026-05-24T12:00",
        end="2026-05-24T18:00",
        timezone="Australia/Melbourne",
        attendee_id="user_1",
        category="lynsey",
    )

    assert payload["all_day"] is False
    assert payload["start_at"] == 1779588000000
    assert payload["end_at"] == 1779609600000
    assert payload["start_timezone"] == "Australia/Melbourne"
    assert payload["end_timezone"] == "Australia/Melbourne"
    assert payload["attendees"] == ["user_1"]
    assert payload["label_id"] == 10


def test_build_timed_event_payload_rejects_end_before_start() -> None:
    try:
        cli.build_timed_event_payload(
            title="Bad",
            start="2026-05-24T18:00",
            end="2026-05-24T12:00",
        )
    except ValueError as exc:
        assert "end must be after start" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_create_timed_uses_safari_path_and_verifies(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_SESSION_COOKIE", "secret-cookie")
    monkeypatch.setenv("TIMETREE_CALENDAR_ID", "cal_1")

    calls: list[dict[str, object]] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})
        if cmd == ["osascript"]:
            class Completed:
                stdout = json.dumps(
                    {
                        "ok": True,
                        "verified": True,
                        "event": {
                            "id": "evt_1",
                            "title": "Lynsey out",
                            "start_at": 1779588000000,
                            "end_at": 1779609600000,
                            "all_day": False,
                            "label_id": None,
                        },
                    }
                )
            return Completed()

        class Completed:
            stdout = ""
        return Completed()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    exit_code = cli.main(
        [
            "create-timed",
            "--title",
            "Lynsey out",
            "--start",
            "2026-05-24T12:00",
            "--end",
            "2026-05-24T18:00",
        ]
    )

    assert exit_code == 0
    assert calls[0]["cmd"][0:2] == ["osascript", "-e"]
    assert calls[1]["cmd"] == ["osascript"]
    script = calls[1]["kwargs"]["input"]
    assert "window.__hermesTimedCreateResult" in script
    assert "credentials:'include'" in script
    assert "1779588000000" in script
    assert json.loads(capsys.readouterr().out) == {
        "event": {
            "all_day": False,
            "end_at": 1779609600000,
            "id": "evt_1",
            "label_id": None,
            "start_at": 1779588000000,
            "title": "Lynsey out",
        },
        "source": "safari",
        "verified": True,
    }


def test_create_timed_requires_calendar_config(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_SESSION_COOKIE", "secret-cookie")
    monkeypatch.delenv("TIMETREE_CALENDAR_ID", raising=False)

    exit_code = cli.main(
        ["create-timed", "--title", "Lynsey out", "--start", "2026-05-24T12:00", "--end", "2026-05-24T18:00"]
    )

    assert exit_code == 2
    assert "TIMETREE_CALENDAR_ID" in capsys.readouterr().err
