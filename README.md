# hermes-timetree-sync

<p align="center">
  <strong>Private TimeTree bridge for Hermes Agent calendar automation.</strong>
</p>

<p align="center">
  <a href="https://github.com/kfa-ai/hermes-timetree-sync/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/kfa-ai/hermes-timetree-sync/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/kfa-ai/hermes-timetree-sync/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/kfa-ai/hermes-timetree-sync?label=release"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.12%2B-blue">
  <img alt="uv" src="https://img.shields.io/badge/package%20manager-uv-654ff0">
  <img alt="Ruff" src="https://img.shields.io/badge/lint-ruff-46a2f1">
  <img alt="Status" src="https://img.shields.io/badge/status-internal-111827">
</p>

`hermes-timetree-sync` is a small Python CLI and client library that lets Hermes create and sync TimeTree calendar events without asking a chat user to open TimeTree.

TimeTree discontinued its official third-party API in December 2023. This project therefore uses TimeTree's current web endpoints through a deliberately narrow, tested client boundary. It is an internal bridge, not an official TimeTree integration; upstream web-app changes may require maintenance.

## Why this exists

The target interaction is simple:

> “Add Day off on May 18.”

Hermes should translate that request into a TimeTree write using locally stored credentials. No browser, TimeTree UI, cookie copying, or OAuth prompt should appear during normal chat usage.

## Capabilities

| Area | Current support |
| --- | --- |
| Auth | Stored TimeTree web session cookie; experimental email/password exchange |
| Discovery | List calendars and labels |
| Reads | Sync calendar events through TimeTree's web sync endpoint |
| Writes | Create, update, and delete events through guarded client methods |
| Hermes UX | Non-interactive all-day event creation, including batch writes |
| Labels | Optional local YAML policy for mapping terms/categories to TimeTree labels |
| Safety | Redacted docs/tests, low-volume API usage, mocked HTTP coverage |

## Installation

```bash
git clone git@github.com:kfa-ai/hermes-timetree-sync.git
cd hermes-timetree-sync
uv sync --dev
```

Run the local quality gates:

```bash
uv run pytest
uv run ruff check .
```

## Configuration

Provide runtime configuration via `.env` or environment variables:

```env
TIMETREE_SESSION_COOKIE=...
TIMETREE_CALENDAR_ID=...
```

- `TIMETREE_SESSION_COOKIE` is the value of TimeTree's `_session_id` browser cookie. Treat it as a bearer secret.
- `TIMETREE_CALENDAR_ID` is the target TimeTree calendar ID for writes.

For local email/password TimeTree accounts, an experimental sign-in command can attempt to exchange credentials for a web session:

```env
TIMETREE_EMAIL=you@example.com
TIMETREE_PASSWORD=...
```

```bash
uv run hermes-timetree-sync sign-in
```

Direct sign-in may fail depending on TimeTree's browser/session checks. Production Hermes usage should rely on a stored, locally refreshed session cookie. See [`docs/authentication.md`](docs/authentication.md).

## CLI quickstart

Check configuration:

```bash
uv run hermes-timetree-sync doctor
```

List calendars:

```bash
uv run hermes-timetree-sync list-calendars
```

Create one all-day event:

```bash
uv run hermes-timetree-sync create-all-day --title "Day off" --date 2026-05-18
```

Create several all-day events with one current-user lookup:

```bash
uv run hermes-timetree-sync create-all-day-batch \
  --event "2026-05-18|Day off" \
  --event "2026-05-25|Public holiday"
```

The batch command was added in `v0.1.1` for faster Hermes calendar writes. It also includes regression coverage for TimeTree accounts whose `/api/v1/user` ID is returned as a number rather than a string.

## Hermes integration model

This package is intentionally UI-free at runtime:

1. A local setup/bootstrap step stores or refreshes `TIMETREE_SESSION_COOKIE` and `TIMETREE_CALENDAR_ID` outside chat.
2. Hermes parses a natural-language calendar request into structured event data.
3. Hermes calls this CLI/client directly.
4. The TimeTree UI is not opened during the user request.

For multiple requested events, Hermes-facing wrappers should prefer `create-all-day-batch` so the current TimeTree user is fetched once and reused for all event attendees.

## Label policy

Create/update helpers can set `label_id` from a local YAML policy instead of hard-coding calendar-specific terms in source code.

```bash
cp timetree-labels.yaml.example timetree-labels.yaml
```

Edit `timetree-labels.yaml` with the target calendar's label IDs and matching terms. The local file is ignored by git.

To use a different policy file:

```bash
export TIMETREE_LABEL_POLICY_FILE=/path/to/timetree-labels.yaml
```

## Security

Never commit or paste into chat:

- TimeTree passwords;
- `_session_id` / `_timetree_session` cookies;
- raw private calendar payloads;
- Google OAuth tokens or other downstream calendar credentials.

Local `.env` files are for development/runtime configuration only. Keep examples, docs, tests, logs, and issue comments sanitized.

## Documentation

- [`docs/authentication.md`](docs/authentication.md) — session-cookie, sign-in, and non-interactive runtime guidance.
- [`docs/reverse-engineered-api.md`](docs/reverse-engineered-api.md) — observed TimeTree web endpoints and payload notes.
- [`docs/roadmap.md`](docs/roadmap.md) — likely next steps and maintenance considerations.
- [`CHANGELOG.md`](CHANGELOG.md) — release history.

## Development notes

When adding endpoint coverage:

- keep TimeTree-specific behavior behind `TimeTreeClient` or narrow CLI helpers;
- prefer mocked HTTP tests over live credentials;
- redact `_session_id`, passwords, cookies, and raw private calendar data;
- run `uv run pytest` and `uv run ruff check .` before publishing changes.

## License

Private/internal project unless a license is added later.
