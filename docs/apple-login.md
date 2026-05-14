# Apple-linked TimeTree login

If your TimeTree account uses **Sign in with Apple**, we do not need to know or store your Apple credentials.

For the first read-only sync slice, use the TimeTree browser session that already exists after you sign in through Apple:

1. Open `https://timetreeapp.com/signin` in a browser.
2. Sign in using Apple.
3. Open browser developer tools.
4. Find cookies for `https://timetreeapp.com`.
5. Copy the value of the TimeTree session cookie. Community projects usually reference `_session_id`; some browser views may show related TimeTree session cookie names.
6. Put the value in local `.env`:

```env
TIMETREE_SESSION_COOKIE=copy-the-cookie-value-here
```

Then test locally:

```bash
uv run hermes-timetree-sync doctor
uv run hermes-timetree-sync list-calendars
```

## Security notes

- Treat the session cookie like a password.
- Do not paste it into chat.
- Do not commit `.env`.
- If a cookie is exposed, sign out of TimeTree / revoke sessions where possible and rotate the local `.env` value.
- Cookies expire; sync should fail clearly and ask for a fresh browser session cookie.

## Why this works for Apple login

Apple handles the identity step in the browser. After successful login, TimeTree sets its own web session cookie. The sync bridge uses that TimeTree session cookie for read-only API calls, so it does not need Apple username/password, Apple 2FA, or an email/password TimeTree login.
