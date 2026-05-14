# TimeTree authentication

The bridge supports two early authentication paths.

## Option A — email/password

Status: the current TimeTree web bundle still contains `PUT /api/v1/auth/email/signin`, but a May 2026 live replay with a known-good password returned HTTP 400 / internal code `-403` even with a fresh `/signin` CSRF token and session cookie. Prefer Option B until this direct login flow is understood.

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

## Option B — browser session cookie

If sign-in is handled by Apple or another browser-only path:

1. Open `https://timetreeapp.com/signin` in a browser.
2. Sign in.
3. Open browser developer tools.
4. Find cookies for `https://timetreeapp.com`.
5. Copy the value of `_session_id`.
6. Put the value in local `.env`:

```env
TIMETREE_SESSION_COOKIE=copy-the-cookie-value-here
```

## Security notes

- Treat the password and session cookie like secrets.
- Do not paste either into chat.
- Do not commit `.env`.
- If either is exposed, rotate the password and sign out/revoke sessions where TimeTree allows.
- Cookies expire; sync should fail clearly and ask for a fresh sign-in/session cookie.
