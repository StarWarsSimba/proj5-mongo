# ACP Brevet Controle Time Calculator with MongoDB (Project 5)

Ajax + Flask + MongoDB reimplementation of the RUSA ACP calculator (https://rusa.org/octime_acp.html). Computes open/close times for each controle via Ajax without page reloads and persists them to MongoDB for later display. Extends Project 4 (https://github.com/StarWarsSimba/proj4-brevets) with `Submit` / `Display` workflow and Docker Compose.

Based on RUSA rules at https://rusa.org/pages/acp-brevet-control-times-calculator / https://rusa.org/octime_alg.html. Skeleton by Michal Young for CIS 322.

## Overview

Brevets are 200/300/400/600/1000 km. Each controle must be reached after its **open** time and before its **close** time. This app lets a rider select a brevet distance, start date/time, and controle distances (miles or km, 20 rows, bidirectional conversion at `DockerMongo/templates/calc.html:147`), then displays open/close times via `GET /_calc_times` (`DockerMongo/app.py:107`, also `DockerMongo/flask_brevets.py:47` standalone) calling `DockerMongo/acp_times.py:20` and `DockerMongo/acp_times.py:51`. Times are ISO 8601 (Arrow) and rendered with `moment.js` as `ddd M/D H:mm`.

**Project 5 additions:**

* **Submit** — `POST /submit` (`DockerMongo/app.py:37`) reads the 20-row form (`miles`, `km`, `location`, `distance`, `begin_date`, `begin_time`), recomputes open/close server-side via `acp_times`, and `insert_many` into MongoDB `brevetdb.controls` (MongoDB service `db:27017` via `DockerMongo/docker-compose.yml:11`, client at `DockerMongo/app.py:14`).
* **Display** — `GET /controls` (`DockerMongo/app.py:31`) reads `db.controls.find({}, {"_id": False})` and renders `DockerMongo/templates/controls.html` with a table of saved controls (brevet distance, start, miles/km, location, open/close). Linked from `calc.html` as "Display saved control times" button.
* **Persistence** — Docker Compose runs two services: `web` (Flask, `python -u app.py`, port `5001:5001`) and `db` (`mongo:7.0`). Data survives across requests via the shared Mongo container.

## ACP Controle Time Rules

All logic is in `DockerMongo/acp_times.py`.

**Valid distances:** `brevet_dist_km` must be 200, 300, 400, 600, or 1000 else `ValueError`. `control_dist_km` must be > 0 else `ValueError`. Controls beyond the brevet are clamped (see below).

**Open time (max speed):** distance `d = min(control, brevet)`:
- 0–200 km: 34 km/h → `min(d,200)/34`
- 200–400 km: 32 km/h → `+ min(d-200,200)/32`
- 400–600 km: 30 km/h → `+ min(d-400,200)/30`
- 600–1000 km: 28 km/h → `+ min(d-600,400)/28`

Rounded to nearest minute: `arrow.get(start).shift(minutes=round(hours*60)).isoformat()`.

**Close time (min speed):**
- 0–60 km: `d/20 + 1` hour (1h grace; e.g., 20 km → 2:00, not 1:20)
- 60–600 km: 15 km/h → `min(d,200)/15 + min(d-200,200)/15 + min(d-400,200)/15`
- 600–1000 km: 11.428 km/h → `+ min(d-600,400)/11.428` (makes 1000 km = 75h)

**French finishing variations** — only when `control == brevet`:
- 200 km finish: 13:30 (not 13:20)
- 400 km finish: 27:00 (not 26:40)
- 300/600/1000 km finishes match the formula (20:00/40:00/75:00). An intermediate 200 km on a 300 km brevet closes at 13:20.

**Beyond brevet:** open clamps when `control > brevet`, close when `control >= brevet` (`DockerMongo/acp_times.py:36`, `DockerMongo/acp_times.py:67`). E.g., 205 km on a 200 km brevet → same as 200 km (open 5:53, close 13:30). Verified against https://rusa.org/octime_acp.html.

**Timezone/rounding:** Input is ISO 8601; Flask builds `begin_date + "T" + begin_time + "-00:00"`. Output preserves that timezone.

**Examples** (start `2024-01-01T00:00+00:00`):

| Brevet | Control | Open | Close | Note |
|--------|---------|------|-------|------|
| 200 | 60 km | 1:46 | 4:00 | 60/34, 60/15 |
| 200 | 200 km | 5:53 | 13:30 | special |
| 400 | 350 km | 10:34 | 23:20 | spans brackets |
| 1000 | 1000 km | 33:05 | 75:00 |  |

## Installation & Running

### With Docker Compose (recommended — includes MongoDB)

```bash
git clone https://github.com/StarWarsSimba/proj5-mongo.git
cd proj5-mongo/DockerMongo
docker compose up --build
# open http://localhost:5001
# to run in background: docker compose up --build -d
# to stop: docker compose down
```

`docker-compose.yml` builds `web` from `Dockerfile` (`FROM python:3.11-slim`, `pip install -r requirements.txt`) and starts `db` (`mongo:7.0`). `web` waits on `db` via `links` and connects with `MongoClient(os.environ.get('DB_PORT_27017_TCP_ADDR', 'db'), 27017)` at `DockerMongo/app.py:14`.

### Without Docker (Flask only, no persistence)

```bash
git clone https://github.com/StarWarsSimba/proj5-mongo.git
cd proj5-mongo
python3 -m venv DockerMongo/.venv && source DockerMongo/.venv/bin/activate
pip install -r DockerMongo/requirements.txt  # flask, pymongo, arrow
cd DockerMongo
python app.py              # or: python app.py --port 5001 --debug
# alternatively standalone calc (no DB): python flask_brevets.py
# open http://localhost:5001
```

Requires a local MongoDB on `localhost:27017` for `POST /submit` / `GET /controls` to work; otherwise `/_calc_times` still works.

**Config** (`DockerMongo/config.py:103`): `DockerMongo/credentials.ini` (`PORT`, `SECRET_KEY`, plus `author`/`repo` under `[DEFAULT]` for grading) overridden by CLI `-D`/`-P`/`-C`. `SECRET_KEY` required for Flask sessions/flash messages.

**Using:** Select brevet distance and start date/time, enter miles or km — the other converts automatically and `calc_times()` (`DockerMongo/templates/calc.html:127`) populates Open/Close via Ajax. Click **Submit control times** to save all non-empty `km` rows (recomputed server-side) to MongoDB — flashes `Saved N control time(s)`. Click **Display saved control times** to view `controls.html`. Errors (no controls entered, non-numeric/negative distances, invalid brevet, malformed date/time) flash on `calc.html` and redirect to `/`.

## API / Routes

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | `calc.html` — calculator form (Ajax) |
| `GET` | `/_calc_times?km=<float>&brevet_distance=<int>&begin_date=YYYY-MM-DD&begin_time=HH:MM` | JSON `{"result":{"open":"...","close":"..."}}` (ISO 8601). Used at `DockerMongo/templates/calc.html:135`. Also directly: `import acp_times; acp_times.open_time(100, 200, "2024-01-01T08:00:00-08:00")` |
| `POST` | `/submit` | Form POST of `distance`, `begin_date`, `begin_time`, lists `miles`/`km`/`location`. Validates, computes open/close, `db.controls.insert_many`. Redirects with flash. |
| `GET` | `/controls` | Renders `controls.html` with all docs from `brevetdb.controls`. |

Example:

```python
import acp_times
acp_times.open_time(100, 200, "2024-01-01T08:00:00-08:00")  # "2024-01-01T10:56:00-08:00"
```

```bash
curl "http://localhost:5001/_calc_times?km=100&brevet_distance=200&begin_date=2024-01-01&begin_time=08:00"
```

## Project Structure

```
proj5-mongo/
  NEWREADME.md
  README.md                # assignment spec
  DockerMongo/
    acp_times.py           # open_time / close_time (RUSA rules)
    app.py                 # Flask app + /_calc_times, POST /submit, GET /controls (MongoDB)
    flask_brevets.py       # standalone Flask app (no DB, for reference)
    config.py              # INI + CLI layering (PORT, SECRET_KEY, author/repo)
    credentials.ini        # [DEFAULT] author, repo, PORT, SECRET_KEY (gitignored)
    requirements.txt       # flask, pymongo, arrow
    docker-compose.yml     # web (build .) + db (mongo:7.0)
    Dockerfile             # FROM python:3.11-slim, pip install, ADD .
    templates/
      calc.html            # 20-row table + Ajax + Submit/Display buttons
      controls.html        # saved controls table
      404.html
    static/
      js/moment.min.js
      css/calc.css
```

## Testing

`acp_times` unit tests (same as Project 4) cover 60 km open, 200 km French close, multi-bracket 350 km, clamping beyond brevet, invalid distance.

Project 5 required tests are the two button workflows:

* **Submit** — with at least one valid `km` row, `POST /submit` inserts to `brevetdb.controls`; with no rows or invalid/negative/non-numeric distances it flashes an error and does not insert.
* **Display** — `GET /controls` returns saved controls (or "No saved control times" when empty).

Manual verification with Docker Compose:

```bash
cd DockerMongo
docker compose up --build -d
# submit via UI then:
curl http://localhost:5001/controls  # should list saved rows
# or via mongo:
docker compose exec db mongosh brevetdb --eval "db.controls.find().toArray()"
docker compose down
```

Direct `acp_times` checks without Docker:

```bash
cd DockerMongo && source .venv/bin/activate
python -c "import acp_times; print(acp_times.open_time(60, 200, '2024-01-01T00:00:00+00:00'))"
python -c "import acp_times; print(acp_times.close_time(200, 200, '2024-01-01T00:00:00+00:00'))"
```

## Docker

```bash
cd DockerMongo
docker compose up --build          # builds web, pulls mongo:7.0, runs on :5001
docker compose down                # stop and remove containers
# single-image build (no DB):
docker build -t brevets-mongo . && docker run -p 5001:5001 brevets-mongo python app.py
```

`Dockerfile` (`DockerMongo/Dockerfile:1`) uses `python:3.11-slim`, installs `requirements.txt`, copies project to `/brevet`. `docker-compose.yml` mounts `.:/todo`, links `web`→`db`, and runs `python -u app.py`.

## References

- https://rusa.org/octime_acp.html, https://rusa.org/octime_alg.html, https://rusa.org/pages/rulesForRiders
- Lecture slides `05a-Table-driven.pdf`, `05b-Docker-Compose.pdf` and `MongoCommands.txt` (Canvas)

## Author

**Miles Gurney** — CIS 322, University of Oregon — `mgurney@uoregon.edu` — [@StarWarsSimba](https://github.com/StarWarsSimba) — https://github.com/StarWarsSimba/proj5-mongo
