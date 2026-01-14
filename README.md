## Pathie

AI-personalized, thematic city tours — fast to generate, engaging to explore.

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](#)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](#)
[![Django](https://img.shields.io/badge/django-5.x-092E20?logo=django&logoColor=white)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)

---

### Table of contents
- [1. Project name](#1-project-name)
- [2. Project description](#2-project-description)
- [3. Tech stack](#3-tech-stack)
- [4. Getting started locally](#4-getting-started-locally)
- [5. Available scripts](#5-available-scripts)
- [6. Project scope](#6-project-scope)
- [7. Project status](#7-project-status)
- [8. License](#8-license)

---

## 1. Project name
Pathie

## 2. Project description
Pathie is a web application that generates thematic, personalized city tour routes using AI. It focuses the MVP on delivering core value: creating and saving routes that are coherent and tailored to a user’s interests, accompanied by unique, narrative-rich descriptions for each place.

- Solves the problem of time-consuming, repetitive, one-size-fits-all itineraries by generating routes based on 1–3 selected interest tags and an optional detailed prompt (1,000–10,000 chars).
- Produces up to 7 suggested points with long-form, context-aware descriptions (2,500–5,000 chars) leveraging Wikipedia and OpenStreetMap.
- Offers a manual mode to search/add points (up to 10), with automatic ordering to form a logical path.
- UI/content is in Polish for the MVP.

Links to planning docs (Polish):
- PRD: [.ai/01-planowanie/05-PRD.md](.ai/01-planowanie/05-PRD.md)
- Simplified tech stack: [.ai/01-planowanie/06-tech-stack-uproszczony.md](.ai/01-planowanie/06-tech-stack-uproszczony.md)

## 3. Tech stack
- Backend/web
  - Python 3.12
  - Django 5 (monolith serving templates + backend)
  - Django Templates + HTMX for progressive interactivity
  - Alpine.js (optional, lightweight client logic)
- Styling
  - Tailwind CSS 4
- Maps
  - Leaflet.js (via `django-leaflet`)
- Data
  - SQLite by default in development
  - PostgreSQL 16 targeted for production
  - Django ORM; Django cache for simple caching
- Auth
  - Django auth (Email/User + Password)
- AI and external services (planned)
  - OpenRouter.ai (LLM for routes and narratives)
  - OpenRouteService (route optimization)
  - Wikipedia API, OpenStreetMap (content/data sources)
- Tooling
  - Testing: `pytest`
  - Lint/format: `ruff`

See declared dependencies in `pathie/pyproject.toml`.

## 4. Getting started locally

### Prerequisites
- Python 3.12+
- Git
- Optional: [`uv`](https://docs.astral.sh/uv/) for fast dependency management

### 1) Clone and enter the project
```bash
git clone <your-repo-url> pathie
cd pathie
```

### 2) Create a virtual environment and install dependencies

Option A — using uv (recommended if available):
```bash
# create & activate venv
uv venv
# on Windows (Git Bash)
source .venv/Scripts/activate
# install from pyproject
uv pip install -e .
```

Option B — using pip:
```bash
python -m venv .venv
# on Windows (Git Bash)
source .venv/Scripts/activate
# install from pyproject
pip install -e .
```

### 3) Initialize the database (SQLite by default)
```bash
python pathie/manage.py migrate
```

Optional (admin access):
```bash
python pathie/manage.py createsuperuser
```

### 4) Run the development server
```bash
python pathie/manage.py runserver
```
Open `http://127.0.0.1:8000/` in your browser. Admin at `http://127.0.0.1:8000/admin/`.

Notes:
- Local dev uses SQLite out-of-the-box. For production, configure PostgreSQL 16 using environment variables and update Django settings accordingly.
- External integrations (OpenRouter.ai, OpenRouteService) require API keys/config that are not set up in this repository yet.

## 5. Available scripts

Django management:
```bash
python pathie/manage.py runserver
python pathie/manage.py migrate
python pathie/manage.py makemigrations
python pathie/manage.py createsuperuser
```

Quality:
```bash
# lint
ruff check .
# format
ruff format .
```

Testing:
```bash
pytest
```

## 6. Project scope

### MVP
- Authentication: email/password signup/login, logout; key actions require login.
- AI-generated routes:
  - 1–3 interest tags + optional 1k–10k char description
  - Up to 7 points per route
  - Per-point, personalized descriptions (2.5k–5k chars) using Wikipedia/OSM
- Manual routes:
  - Search/add points on an interactive map (up to 10)
  - Automatic ordering optimization
- Interaction:
  - Dual view: list + map (responsive, mobile-first)
  - Remove points before saving
  - “Show my location” (one-shot)
  - “Navigate to” opens external map app
  - Offline cache of loaded route and descriptions
- Route management:
  - Temporary routes until saved
  - Auto-generated name with later rename
  - List, view, delete saved routes
- Feedback:
  - Thumbs up/down per place description
  - Overall route rating

## 7. Project status
- Status: early MVP scaffolding; core features to be implemented iteratively.
- Success metrics (from PRD):
  - 70% of AI-generated routes “accepted” (saved or used to navigate).
  - 70% positive ratings on generated place descriptions.

## 8. License
The project is licensed under the MIT license.