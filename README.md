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

## TimeTree label policy

Create/update helpers can set `label_id` from a local YAML policy instead of hard-coding calendar-specific terms in code.

1. Copy the example:

   ```bash
   cp timetree-labels.yaml.example timetree-labels.yaml
   ```

2. Edit `timetree-labels.yaml` with your calendar's label IDs and matching terms. The local file is ignored by git.

3. Optionally point at a different file:

   ```bash
   export TIMETREE_LABEL_POLICY_FILE=/path/to/timetree-labels.yaml
   ```

## Development

This repo starts as a Python CLI/library.

```bash
uv sync --dev
uv run pytest
```

Early commands:

```bash
uv run hermes-timetree-sync doctor
uv run hermes-timetree-sync list-calendars
uv run hermes-timetree-sync create-all-day --title "Day off" --date 2026-05-18
```

Hermes-facing usage is non-interactive: once `TIMETREE_SESSION_COOKIE` and `TIMETREE_CALENDAR_ID` are configured, Hermes can translate a request like “add Day off on May 18” into the CLI call above without visiting the TimeTree UI. See [`docs/authentication.md`](docs/authentication.md).

## Security

Do not commit:

- TimeTree email/password;
- `_session_id` / `_timetree_session` cookies;
- raw API responses containing private calendar data;
- Google OAuth tokens.

Use `.env` locally; keep `.env.example` as documentation only.
