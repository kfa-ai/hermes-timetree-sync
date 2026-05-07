# Roadmap

## Milestone 1 — read-only TimeTree client

- Add `TimeTreeClient` with injected `httpx.Client`.
- Support session-cookie auth from env.
- Implement:
  - list calendars;
  - list labels for a calendar;
  - sync events for a calendar.
- Add unit tests from redacted fixtures.

## Milestone 2 — event model and ICS export

- Normalize TimeTree event payloads into internal models.
- Handle all-day and timed events.
- Preserve stable IDs.
- Emit `.ics` for one selected calendar.

## Milestone 3 — Google Calendar mirror

- Add Google Calendar adapter.
- Create/update/delete mirrored events in a dedicated mirror calendar.
- Store sync state locally or in a small durable store.

## Milestone 4 — Hermes integration

- Expose the mirrored Google calendar to Hermes.
- Add scheduled sync with structured logs.
- Add alerts for expired auth and endpoint/schema changes.

## Deferred — TimeTree writes

Direct writes to TimeTree are out of scope until read-only sync is reliable. If explored, implement behind explicit feature flags and require manual review.
