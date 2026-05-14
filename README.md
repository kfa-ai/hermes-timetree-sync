# hermes-timetree-sync

A small Python CLI and client library for connecting Hermes to TimeTree via TimeTree's current web endpoints.

The project is intentionally conservative: TimeTree discontinued its official third-party API in December 2023, so this bridge treats all TimeTree access as unofficial, private API usage. It keeps that logic isolated behind a narrow client boundary, uses low request volume, and never requires Hermes chat sessions to visit the TimeTree UI.

## What it does

Current `0.1.x` capabilities:

- authenticate with a stored TimeTree web session cookie;
- experimentally exchange a local email/password credential for a web session;
- list calendars and labels;
- fetch/sync events from a TimeTree calendar;
- create and update events through guarded helper methods;
- create non-interactive all-day events from Hermes, for example `Day off` on a specific date;
- apply optional local label policy matching from YAML.

This is not an official TimeTree integration. Upstream endpoint changes may require maintenance.

## Installation

```bash
git clone git@github.com:kfa-ai/hermes-timetree-sync.git
cd hermes-timetree-sync
uv sync --dev
```

Run checks:

```bash
uv run pytest
uv run ruff check .
```

## Configuration

Create a local `.env` file or provide environment variables directly:

```env
TIMETREE_SESSION_COOKIE=...
TIMETREE_CALENDAR_ID=...
```

`TIMETREE_SESSION_COOKIE` is the value of TimeTree's `_session_id` browser cookie. Treat it as a bearer secret.

For a local email/password account, the experimental sign-in flow can be used to obtain a session cookie:

```env
TIMETREE_EMAIL=you@example.com
TIMETREE_PASSWORD=...
```

```bash
uv run hermes-timetree-sync sign-in
```

Direct sign-in can fail depending on TimeTree's browser/session checks. The preferred production path is a stored session cookie, refreshed outside normal chat requests. See [`docs/authentication.md`](docs/authentication.md).

## CLI usage

Check local configuration:

```bash
uv run hermes-timetree-sync doctor
```

List accessible calendars:

```bash
uv run hermes-timetree-sync list-calendars
```

Create an all-day event:

```bash
uv run hermes-timetree-sync create-all-day --title "Day off" --date 2026-05-18
```

For Hermes, the expected runtime model is non-interactive: once `TIMETREE_SESSION_COOKIE` and `TIMETREE_CALENDAR_ID` are configured locally, Hermes can translate a user request such as “add Day off on May 18” into the CLI/API call without opening TimeTree in a browser.

## Label policy

Create/update helpers can set `label_id` from a local YAML policy instead of hard-coding calendar-specific terms in code.

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

Local `.env` files are for development/runtime configuration only. Keep `.env.example` and documentation sanitized.

## Development notes

Useful commands:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

Private API behavior and authentication findings are documented in:

- [`docs/authentication.md`](docs/authentication.md)
- [`docs/reverse-engineered-api.md`](docs/reverse-engineered-api.md)
- [`docs/roadmap.md`](docs/roadmap.md)

When adding endpoint coverage, prefer small client methods with mocked tests and redacted fixtures. Keep TimeTree-specific assumptions out of Hermes-facing code wherever possible.

## License

Private/internal project unless a license is added later.
