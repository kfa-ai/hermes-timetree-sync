# Changelog

## v0.1.1 - 2026-05-15

Small speed/reliability release for Hermes calendar writes.

### Added

- `create-all-day-batch` CLI command to create multiple all-day events with one current-user lookup.

### Fixed

- Accept numeric TimeTree current-user IDs and stringify them when building event attendees.
- Added regression coverage for batch event creation and numeric current-user IDs.

## v0.1.0 - 2026-05-14

Initial release of the Hermes TimeTree bridge.

### Added

- TimeTree web API client with session-cookie authentication.
- Experimental email/password sign-in command for local credential exchange.
- Calendar, label, current-user, event-sync, create, and update client methods.
- Non-interactive all-day event creation command for Hermes use cases.
- Local YAML label policy support.
- Authentication and reverse-engineered API documentation.
- Pytest and Ruff validation.

### Notes

- TimeTree's official third-party API is discontinued; this release uses unofficial web endpoints and may need maintenance if TimeTree changes its web app.
- `_session_id` values are bearer secrets and must stay in local runtime configuration only.
