# hermes-timetree-sync

A managed, cautious TimeTree sync bridge for Hermes.

## Goal

Build a small service/CLI that can read TimeTree calendar data through currently available unofficial web/internal endpoints, mirror it into a stable calendar surface such as Google Calendar or ICS, and eventually expose safe hooks for Hermes.

## Current stance

TimeTree discontinued its official third-party API in December 2023. This project therefore treats TimeTree access as **unofficial and brittle**:

- prefer read-only mirroring first;
- keep request volume low;
- never commit credentials or session cookies;
- isolate TimeTree-specific reverse-engineered code behind a small client boundary;
- prefer Google Calendar / ICS as the stable integration surface for Hermes.

## Proposed phases

1. **Read-only discovery**
   - Authenticate using a session cookie or email/password flow only in local/dev environments.
   - List calendars and labels.
   - Fetch events from a selected calendar.
   - Save raw fixtures with sensitive values redacted.

2. **ICS export**
   - Convert TimeTree events to `.ics`.
   - Support one calendar initially.
   - Add deterministic IDs and update semantics.

3. **Google Calendar mirror**
   - Push/update mirrored events into a dedicated Google Calendar.
   - Make Google Calendar the interface Hermes reads from.

4. **Operational bridge**
   - Scheduled sync with observability.
   - Low-frequency polling.
   - Clear errors for expired cookies or upstream endpoint changes.

5. **Writes, only if justified**
   - Investigate create/update/delete endpoints separately.
   - Keep disabled by default.
   - Require explicit acceptance of brittleness/risk.

## Known unofficial endpoint shape

Base URL:

```text
https://timetreeapp.com/api/v1
```

Endpoints observed in public community projects:

```text
PUT /auth/email/signin
GET /calendars?since=0
GET /calendar/{calendar_id}/events/sync
GET /calendar/{calendar_id}/events/sync?since={since}
GET /calendar/{calendar_id}/labels
```

Public calendars:

```text
https://timetreeapp.com/api/v2/public_calendars/{calendar_id}/public_events
```

## Development

This repo starts as a Python CLI/library.

```bash
uv sync --dev
uv run pytest
```

Early read-only commands:

```bash
uv run hermes-timetree-sync doctor
uv run hermes-timetree-sync list-calendars
```

If your TimeTree account is tied to Apple login, use a browser session cookie rather than Apple credentials. See [`docs/apple-login.md`](docs/apple-login.md).

## Security

Do not commit:

- TimeTree email/password;
- `_session_id` / `_timetree_session` cookies;
- raw API responses containing private calendar data;
- Google OAuth tokens.

Use `.env` locally; keep `.env.example` as documentation only.
