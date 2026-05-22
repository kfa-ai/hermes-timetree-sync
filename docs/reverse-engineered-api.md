# Reverse-engineered TimeTree web API notes

Observed against `https://timetreeapp.com` from an authenticated Safari web session in May 2026. This is unofficial/private API behavior and may change without notice.

## Request basics

Base URL:

```text
https://timetreeapp.com/api
```

The current web bundle builds requests with:

```text
X-TimeTreeA: web/2.1.0/<locale-or-code>
X-CSRF-Token: <meta name="csrf-token" content="...">
Content-Type: application/json
credentials: include
```

For read-only calls from an already authenticated browser, the important credential is the HttpOnly `_session_id` cookie. It is not visible via `document.cookie`, but browser `fetch(..., {credentials: "include"})` sends it.

## Auth/session observations

The bundle still defines:

```text
PUT /api/v1/auth/email/signin
body: {"uid": email, "password": password, "uuid": device_uuid}
```

Live replay with a known-good password returned:

```text
HTTP 400
{"error":{"code":-403,"message":"failed to api request","params":{}}}
```

This means direct email/password exchange is not yet reliable. Browser-session capture/reuse is the safer initial path.

## Endpoints verified from authenticated Safari session

### List auth methods

```text
GET /api/v1/auths
```

Shape:

```json
{"auths": {"email": {}, "facebook": {}, "apple": {}, "google": {}}}
```

### List calendars

```text
GET /api/v1/calendars
```

Shape:

```json
{
  "calendars": [
    {
      "id": 123456789,
      "alias_code": "...",
      "type": "...",
      "name": "...",
      "note": "...",
      "author_id": 123,
      "color": "...",
      "badge": "...",
      "background_image_url": "...",
      "purpose": "...",
      "permission": "...",
      "enable_chat": true,
      "deactivated_at": null,
      "updated_at": 123,
      "created_at": 123,
      "unread_count": 0,
      "push_alert": true,
      "alert_filter_attendee": false,
      "summarized_push_notification_local_time": null,
      "summarized_push_notification_timezone": null
    }
  ],
  "since": 123
}
```

### List calendar labels

```text
GET /api/v1/calendar/{calendar_id}/labels
```

Shape:

```json
{
  "since": 123,
  "calendar_labels": [
    {
      "id": 1,
      "calendar_id": 123456789,
      "name": "...",
      "color": "...",
      "order": 1,
      "default_color": "...",
      "updated_at": 123,
      "created_at": 123
    }
  ]
}
```

Note: the key is `calendar_labels`, not `labels`.

### Sync events

```text
GET /api/v1/calendar/{calendar_id}/events/sync
GET /api/v1/calendar/{calendar_id}/events/sync?since={cursor}
```

Observed shape:

```json
{
  "since": 1746775344141,
  "chunk": true,
  "events": [
    {
      "id": "...",
      "primary_id": "...",
      "calendar_id": 123456789,
      "uuid": "...",
      "category": 0,
      "type": 0,
      "author_id": 123,
      "author_type": "...",
      "title": "...",
      "all_day": false,
      "start_at": 123,
      "start_timezone": "UTC",
      "end_at": 123,
      "end_timezone": "UTC",
      "label_id": 1,
      "location": "...",
      "location_lat": null,
      "location_lon": null,
      "url": null,
      "note": null,
      "lunar": false,
      "attendees": [],
      "recurrences": [],
      "recurring_uuid": null,
      "alerts": [],
      "parent_id": null,
      "link_object_id": null,
      "link_object_id_string": null,
      "row_order": null,
      "attachment": {"virtual_user_attendees": []},
      "like_count": 0,
      "files": [],
      "media_content_count": 0,
      "deactivated_at": null,
      "pinned_at": null,
      "updated_at": 123,
      "created_at": 123
    }
  ]
}
```

One live call returned exactly 300 events with `chunk: true`, suggesting the client must keep syncing with the returned `since` cursor until `chunk` is false or no events remain.

### Create event

Verified once with explicit user approval for a single all-day event:

```text
POST /api/v1/calendar/{calendar_id}/event
```

Minimal all-day schedule body that succeeded:

```json
{
  "title": "Example all-day event",
  "all_day": true,
  "start_at": 1779062400000,
  "start_timezone": "UTC",
  "end_at": 1779062400000,
  "end_timezone": "UTC",
  "category": 1,
  "type": 0,
  "label_id": 1,
  "attendees": ["<current-user-id>"],
  "alerts": [900],
  "recurrences": [],
  "location": "",
  "location_lat": null,
  "location_lon": null,
  "url": null,
  "note": null,
  "attachment": {"virtual_user_attendees": []},
  "files": []
}
```

Notes:
- For a single-day all-day event, TimeTree uses the same UTC-midnight timestamp for `start_at` and `end_at`.
- `attendees` should include the current user ID from `GET /api/v1/user`; do not hard-code the example ID above.
- The current-user `id` may be returned as either a JSON string or number. Hermes-facing helpers stringify numeric IDs before putting them in `attendees`.
- Response shape was `{ "event": {...}, "rebalanced": ... }`.
- Creation was verified by reading back `/events/sync` and matching title/date/all-day fields.

### Create timed event via Safari page context

The local `create-timed` CLI command uses the same `POST /api/v1/calendar/{calendar_id}/event` endpoint, but executes it in Safari's authenticated TimeTree page context rather than direct `httpx` replay. The request body differs from all-day events:

```json
{
  "title": "Example timed event",
  "all_day": false,
  "start_at": 1779588000000,
  "start_timezone": "Australia/Melbourne",
  "end_at": 1779609600000,
  "end_timezone": "Australia/Melbourne",
  "category": 1,
  "type": 0,
  "label_id": 10,
  "attendees": ["<current-user-id>"],
  "alerts": [],
  "recurrences": [],
  "location": "",
  "location_lat": null,
  "location_lon": null,
  "url": null,
  "note": null,
  "attachment": {"virtual_user_attendees": []},
  "files": []
}
```

The CLI fetches `/api/v1/user` in Safari to fill `attendees`, posts the event with `credentials: include`, then verifies via `/events/sync` by matching event ID/title/start/end and `all_day: false`. Safari must be logged into TimeTree and have Develop → Allow JavaScript from Apple Events enabled.
- Library create/update helpers can apply a YAML-driven TimeTree label policy by adding `label_id` from an explicit category or inferred title/note.
- `create-all-day-batch` is a local CLI batching helper, not a separate TimeTree batch endpoint. It performs one current-user lookup and then one `POST /event` per requested all-day event.

### Label policy

Calendar-specific label conventions are intentionally kept out of source code. Configure them locally with `timetree-labels.yaml` or `TIMETREE_LABEL_POLICY_FILE`. The committed `timetree-labels.yaml.example` shows the schema:

```yaml
rules:
  - category: example-medical
    colour: blue
    label_id: 3
    terms:
      - doctor
      - clinic
```

`label_id` values can be discovered from:

```text
GET /api/v1/calendar/{calendar_id}/labels
```

### Update event

Verified once with explicit user approval against an all-day event created as a test fixture:

```text
PUT /api/v1/calendar/{calendar_id}/event/{event_id}
```

A minimal partial title update succeeded:

```json
{"title": "Example all-day event - updated"}
```

Observed behavior:
- The request succeeded with HTTP 200.
- Response shape was `{ "event": {...}, "rebalanced": ... }`.
- A follow-up `/events/sync` read verified the same event ID had the updated title while retaining the all-day date fields.

### Delete event

Verified once with explicit user approval against the test all-day event created above:

```text
DELETE /api/v1/calendar/{calendar_id}/event/{event_id}
```

Observed behavior:
- The request succeeded with HTTP 200.
- The response body was an empty JSON object: `{}`.
- A full `/events/sync` read afterwards found zero active matching records for the deleted event ID/title/date.

## Local storage clues

The web app stores current calendar IDs in:

```text
localStorage["timetree.currentCalendarIds"] = "[123456789]"
```

It also stores a generated app UUID under `localStorage["timetree"]`.
