# Cora Leaderboard — Product & Developer Overview

Cora Leaderboard is a cycling competition platform that integrates with Strava. Athletes authenticate via Strava OAuth, and the system automatically tracks their times on predefined Strava segments. Per-challenge results and a full-season general classification are computed and exposed via a REST API consumed by the accompanying frontend.

The competition format mirrors road cycling: each two-week challenge features one sprint segment and one climb segment. Athletes accumulate points (top-8 per challenge earn 15, 12, 10, 8, 6, 4, 2, 1 points) and the best 8 results per category count toward the season standings.

---

## Architecture

```txt
Frontend (React/Vite)  ──►  REST API (Flask/Python)  ──►  PostgreSQL
                                      │
                                      ▼
                               Strava API (OAuth + Webhooks)
```

| Layer | Stack |
|-------|-------|
| Backend | Python 3, Flask, SQLAlchemy |
| Database | PostgreSQL |
| External | Strava API v3 (OAuth 2.0, webhooks) |
| Frontend | React, TypeScript, Vite, Tailwind CSS |

---

## Core Concepts

### Challenge

A two-week competition window with exactly two Strava segments assigned: one sprint and one climb. Multiple challenges make up a season (year).

### Segment

A Strava-defined route section identified by its Strava segment ID. Metadata (name, distance, elevation gain) is fetched from the Strava API on first use and stored locally.

### Effort

A single timed run by an athlete on a segment, recorded via Strava webhook when an activity is uploaded. Only the best effort per athlete per segment per challenge counts.

### Classification

Season-wide standings aggregated across all challenges for a given year. Sprint and climb points are tracked separately. Only the top 8 challenge results per category per athlete count toward the total.

---

## Data Model

```txt
athletes          challenges               segments
──────────        ──────────               ────────
id (Strava ID)    id                       id (Strava segment ID)
firstname         climb_segment_id ──►     name
lastname          sprint_segment_id ──►    distance
sex               start_date               elevation_gain
access_token*     end_date
refresh_token*
expires_at

efforts
───────
id
athlete_id ──► athletes.id
activity_id
segment_id ──► segments.id
start_date
elapsed_time
```

`*` Tokens are encrypted at rest using AES-256-GCM.

---

## API Endpoints

All routes are served under the `/api` prefix.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/health/db` | Database connectivity check |
| `GET` | `/athletes` | List all registered athletes |
| `GET` | `/challenges?y=<year>` | List challenges for a year with status (`upcoming` / `active` / `completed`) |
| `POST` | `/challenges` | Create a new challenge; segments are fetched from Strava automatically |
| `GET` | `/challenges/<id>` | Get a single challenge |
| `GET` | `/challenges/<id>/results?segment_type=&gender=` | Ranked results for a challenge |
| `GET` | `/classification?gender=&y=<year>` | Season-wide standings |
| `GET` | `/exchange_token?code=&scope=` | Strava OAuth callback — registers or updates an athlete |
| `GET` | `/webhook` | Strava webhook subscription verification |
| `POST` | `/webhook` | Receives Strava activity events (create / update / delete) |

### Webhook event handling

| Strava event | Action |
|---|---|
| `activity/create` | Fetch full activity from Strava, extract matching segment efforts, persist |
| `activity/update` (made private) | Delete stored efforts for that activity |
| `activity/update` (made public) | Re-add efforts for that activity |
| `activity/delete` | Delete stored efforts for that activity |
| `athlete/update` (deauthorized) | Remove athlete and all their efforts |

---

## Authentication & Security

-   Athletes log in via **Strava OAuth 2.0** (required scope: `activity:read`).
-   Access and refresh tokens are **encrypted at rest** (AES-256-GCM, versioned format `v1$<base64>`).
-   Tokens are refreshed transparently when expired before any outbound Strava API call.
-   Webhook requests from Strava are verified using `STRAVA_VERIFY_TOKEN`.

---

## Configuration

The application is configured via environment variables:

| Variable | Description |
|---|---|
| `CLIENT_ID` | Strava application client ID |
| `CLIENT_SECRET` | Strava application client secret |
| `DATABASE_URL` | PostgreSQL connection string |
| `STRAVA_VERIFY_TOKEN` | Secret token used to verify Strava webhook subscriptions |
| `TOKEN_ENC_KEY` | Base64-encoded 32-byte key for AES token encryption |
| `FLASK_ENV` | `development` or `production` |
| `FRONTEND_URL` | Allowed CORS origin (production only) |

**Scoring constants** (defined in `backend/config.py`):

-   `POINTS = [15, 12, 10, 8, 6, 4, 2, 1]` — points awarded for positions 1–8.
-   `MAX_COUNTED_RESULTS = 8` — maximum challenge results counted per athlete per category toward the season classification.

---

## Local Development

**Prerequisites:** Python 3.11+, PostgreSQL (or Docker), a registered Strava application.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # macOS/Linux

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Set environment variables (see Configuration section above)

# 4. Start the API
python backend/run.py
```

The API will be available at `http://localhost:5000`.

For the **database**, a Docker container can be started via the `Start local database` VS Code task.

For the **frontend**, see the separate `cora-leaderboard-frontend` repository.

---

## Project Structure

```
backend/
├── run.py                  # Entry point
├── config.py               # Environment-based config, scoring constants
└── app/
    ├── __init__.py         # App factory, CORS, teardown hooks
    ├── database.py         # SQLAlchemy session management, retry decorator
    ├── helpers.py          # TimeSpan, Gender utilities
    ├── api/
    │   └── routes/         # Flask route handlers (one file per domain)
    ├── models/             # SQLAlchemy ORM models
    └── services/           # Business logic and repository classes
        ├── athlete.py      # Athlete CRUD + token refresh
        ├── challenge.py    # Challenge CRUD + active challenge lookup
        ├── segment.py      # Segment CRUD + Strava metadata fetch
        ├── effort.py       # Effort ingestion, filtering, deletion
        ├── results.py      # Per-challenge ranking and points assignment
        ├── classification.py  # Season-wide standings aggregation
        └── utilities.py    # Token encryption/decryption
```

---

## Known Issues / TODOs

-   Segment metadata is fetched using a **hardcoded admin athlete ID** (`17596625`) to obtain a valid Strava access token. This should be replaced with a dedicated service account or app-level token flow.
