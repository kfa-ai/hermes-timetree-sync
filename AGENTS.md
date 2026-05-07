# AGENTS.md

Repository guidance for agents working on `hermes-timetree-sync`.

## Purpose

This repo is a managed TimeTree-to-Hermes bridge. TimeTree has no active official third-party API, so all TimeTree direct access must be treated as unofficial, brittle, and security-sensitive.

## Rules

- Prefer read-only sync before writes.
- Do not commit credentials, session cookies, raw private calendar payloads, or Google OAuth tokens.
- Keep reverse-engineered TimeTree API access isolated in a small client module.
- Add tests around payload parsing and event normalization before broadening endpoint coverage.
- Use fixtures with private data redacted.
- Keep request frequency low and avoid aggressive polling.

## Commands

```bash
uv sync --dev
uv run ruff check .
uv run pytest
uv run hermes-timetree-sync doctor
uv run hermes-timetree-sync sign-in
uv run hermes-timetree-sync list-calendars
```
