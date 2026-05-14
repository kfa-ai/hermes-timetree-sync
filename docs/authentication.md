# TimeTree authentication

The bridge is designed for non-interactive Hermes use. Normal operation should be: Hermes receives a request like “add Day off on May 18” and calls the CLI/API directly; no TimeTree UI visit is part of the day-to-day workflow.

A valid TimeTree web session is still required somewhere in local configuration. Treat `_session_id` as a bearer secret.

## Preferred path — stored web session

Configure these locally:

```env
TIMETREE_SESSION_COOKIE=copy-the-cookie-value-here
TIMETREE_CALENDAR_ID=your-calendar-id
```

Then Hermes can use commands such as:

```bash
uv run hermes-timetree-sync list-calendars
uv run hermes-timetree-sync create-all-day --title "Day off" --date 2026-05-18
uv run hermes-timetree-sync create-all-day-batch \
  --event "2026-05-18|Day off" \
  --event "2026-05-25|Public holiday"
```

Prefer `create-all-day-batch` when a Hermes request contains multiple events. It creates each event with a single shared current-user lookup, which makes chat-driven writes faster and avoids repeated `/api/v1/user` calls.

If the session expires, refresh the stored session outside chat and rerun `doctor`/`list-calendars` to validate it.

## Experimental fallback — email/password

Status: the current TimeTree web bundle still contains `PUT /api/v1/auth/email/signin`, but a May 2026 live replay with a known-good password returned HTTP 400 / internal code `-403` even with a fresh `/signin` CSRF token and session cookie. Do not rely on this as the primary Hermes auth path.

If your TimeTree account has a normal username/password, configure these locally:

```env
TIMETREE_EMAIL=you@example.com
TIMETREE_PASSWORD=your-password
```

Then exchange them for a TimeTree web session cookie:

```bash
uv run hermes-timetree-sync sign-in
```

The command prints:

```env
TIMETREE_SESSION_COOKIE=...
```

Copy that value into `.env` and then run read-only commands:

```bash
uv run hermes-timetree-sync list-calendars
```

For least local secret exposure, you can remove `TIMETREE_PASSWORD` from `.env` after generating a session cookie.

## Manual browser-cookie refresh

If direct sign-in does not work and no reusable local session is available, refresh `TIMETREE_SESSION_COOKIE` outside Hermes:

1. Open `https://timetreeapp.com/signin` in a browser.
2. Sign in.
3. Open browser developer tools.
4. Find cookies for `https://timetreeapp.com`.
5. Copy the value of `_session_id`.
6. Put the value in local `.env`.

This is an operational fallback, not the intended per-request Hermes flow.

## Security notes

- Treat the password and session cookie like secrets.
- Do not paste either into chat.
- Do not commit `.env`.
- If either is exposed, rotate the password and sign out/revoke sessions where TimeTree allows.
- Cookies expire; sync should fail clearly and ask for a fresh sign-in/session cookie.
