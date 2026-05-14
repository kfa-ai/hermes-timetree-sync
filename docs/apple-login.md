# Apple-linked TimeTree login

If your TimeTree account uses **Sign in with Apple**, this bridge still does not need Apple credentials.

Apple performs the identity step in the browser. After successful login, TimeTree sets its own web session cookie. The sync bridge uses that TimeTree session cookie for private TimeTree web endpoints, so it does not need Apple username/password, Apple 2FA, or a separate TimeTree email/password login.

## Runtime model

Normal Hermes usage should remain non-interactive: once a valid TimeTree session cookie and calendar ID are stored locally, Hermes can create events without opening TimeTree.

Required local values:

```env
TIMETREE_SESSION_COOKIE=copy-the-cookie-value-here
TIMETREE_CALENDAR_ID=your-calendar-id
```

Then test locally:

```bash
uv run hermes-timetree-sync doctor
uv run hermes-timetree-sync list-calendars
uv run hermes-timetree-sync create-all-day --title "Day off" --date 2026-05-18
```

For multiple events from one Hermes request, prefer:

```bash
uv run hermes-timetree-sync create-all-day-batch \
  --event "2026-05-18|Day off" \
  --event "2026-05-25|Public holiday"
```

`create-all-day-batch` is a local convenience command: it fetches the current TimeTree user once, stringifies numeric user IDs when needed, and then creates each all-day event individually.

## Manual browser-session fallback

If no automated local session bootstrap is available:

1. Open `https://timetreeapp.com/signin` in a browser.
2. Sign in using Apple.
3. Open browser developer tools.
4. Find cookies for `https://timetreeapp.com`.
5. Copy the value of `_session_id`.
6. Store the value in local runtime configuration only.

This is an operational fallback, not the intended per-request Hermes flow.

## Security notes

- Treat the session cookie like a password.
- Do not paste it into chat.
- Do not commit `.env`.
- If a cookie is exposed, sign out of TimeTree / revoke sessions where possible and rotate the local runtime value.
- Cookies expire; sync should fail clearly and ask for a fresh session cookie or local bootstrap refresh.
