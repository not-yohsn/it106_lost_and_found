> **Note:** The single source of truth for project scope, objectives, and architecture is now [README.md](README.md). This document is preserved as a build-history log and risk register for the original Milestones 1–8 that delivered the application itself.

---

# ScopeProject — Lost and Found Tracking System

> Source brief: [LOST-AND-FOUND.pdf](LOST-AND-FOUND.pdf)
> Existing prototypes: [prototype.html](prototype.html) (ERD), [chatbot_prototype.html](chatbot_prototype.html)

---

## 1. Project Overview

A **web-based Lost and Found Tracking System** that replaces the current ad-hoc workflow (Facebook posts, Student Local Government Office logs) with a single, centralized platform. The system lets students report lost items, lets staff log found items, automatically matches the two, and notifies the owner when a match is detected.

**Goal:** Reduce delays in returning items, eliminate scattered records, and provide real-time status tracking.

---

## 2. Problem → Solution

| Current Pain Point                         | System Response                              |
| ------------------------------------------ | -------------------------------------------- |
| Lost items posted on social media          | Centralized lost-item reporting form         |
| Reports go to SLG Office only              | Single source of truth, accessible online    |
| No centralized tracking system             | Database with item status workflow           |
| Delays in returning items                  | Automatic match alerts + notifications       |
| Risk of lost records / misinformation      | Persistent storage with audit history        |

---

## 3. Scope

### In Scope (MVP)
- User registration & authentication (student / staff / admin roles)
- Submit a **Lost Report** (name, description, photo, location, date)
- Log a **Found Item** (description, photo, location found, date)
- **Match engine** — keyword + category + date-range matching of lost vs. found
- **Claim** workflow — owner verifies ownership before release
- Real-time **status tracking** (Reported → Matched → Claimed → Closed)
- Email / in-app **notifications** on match and on claim approval
- Optional: chatbot assistant (prototype already exists)

### Out of Scope (v1)
- Mobile native apps (web is responsive; mobile can come later)
- Payment / reward features
- Off-campus / public-facing deployment
- AI image-based matching (text matching only for v1)

---

## 4. User Roles

| Role     | Capabilities                                                                    |
| -------- | ------------------------------------------------------------------------------- |
| Student  | Register, file lost reports, browse found items, submit claims                  |
| Finder   | Submit found items (can be a student or anyone)                                 |
| Staff    | Log found items received at the office, review & verify claims                  |
| Admin    | Manage users, oversee matches, generate reports                                 |

---

## 5. Core Modules

1. **Auth Module** — sign up, login, role-based access
2. **Reporting Module** — lost item form, found item form, image upload
3. **Match Module** — automated matching + manual override by staff
4. **Claim Module** — claim submission, identity verification, release log
5. **Notification Module** — email + on-site notifications
6. **Dashboard** — per-role views with stats and item lists
7. **Chatbot Helper** *(optional)* — guides users through reporting

---

## 6. Data Model

Pulled from the ERD in [prototype.html](prototype.html):

| Entity         | Purpose                                                  |
| -------------- | -------------------------------------------------------- |
| `USER`         | Account owner — student, staff, finder, or admin         |
| `LOST_REPORT`  | An item reported missing by a user                       |
| `FOUND_ITEM`   | An item turned in / logged by a finder or staff          |
| `FINDER`       | Person who turned in a found item (may be unregistered)  |
| `MATCH`        | Link between a `LOST_REPORT` and a `FOUND_ITEM`          |
| `CLAIM`        | Owner's request to recover a matched item, with verifier |

**Key relationships:**
- `USER` 1—N `LOST_REPORT`
- `FINDER` 1—N `FOUND_ITEM`
- `LOST_REPORT` 1—1 `MATCH` ↔ `FOUND_ITEM`
- `MATCH` 1—N `CLAIM`
- `USER` (staff) verifies `CLAIM` (1—N)

---

## 7. Tech Stack (Locked)

| Layer        | Choice                                            |
| ------------ | ------------------------------------------------- |
| Frontend     | HTML + CSS + **Bootstrap 5** + vanilla JS         |
| Templating   | Jinja2 (built into Flask)                         |
| Backend      | **Python 3.11+** with **Flask 3**                 |
| ORM          | SQLAlchemy via Flask-SQLAlchemy                   |
| Auth         | Flask-Login + Werkzeug password hashing           |
| Forms / CSRF | Flask-WTF + WTForms                               |
| Database     | **MySQL 8 (local)** — XAMPP or MySQL Installer    |
| DB driver    | PyMySQL                                           |
| File upload  | Local `app/static/uploads/`                       |
| Email        | Flask-Mail (added in Milestone 5)                 |
| Hosting      | Local now → PythonAnywhere / Render later         |

> Static prototypes ([prototype.html](prototype.html), [chatbot_prototype.html](chatbot_prototype.html)) stay as design reference. The live app uses Jinja templates styled with Bootstrap.

---

## 8. Tools & Software

Single source of truth for everything used to build, run, and ship this project. Treat the first two tables as a setup checklist.

### 8.1 Development Software (install once)

| Tool             | Purpose                              | Where to get it                                  |
| ---------------- | ------------------------------------ | ------------------------------------------------ |
| **Python 3.11+** | Backend runtime                      | https://www.python.org/downloads/ — tick **Add to PATH** during install |
| **XAMPP**        | Bundles MySQL 8 + phpMyAdmin         | https://www.apachefriends.org/                   |
| **Git**          | Version control                      | https://git-scm.com/downloads                    |
| **VS Code**      | Code editor                          | https://code.visualstudio.com/                   |
| **Web browser**  | Run the app + use built-in dev tools | Chrome / Edge / Firefox                          |

### 8.2 VS Code Extensions (recommended)

| Extension                | Why                                            |
| ------------------------ | ---------------------------------------------- |
| Python (Microsoft)       | Linting, debugging, virtualenv detection       |
| Pylance                  | Type hints + autocomplete                      |
| Jinja (wholroyd)         | Syntax highlighting for `.html` templates      |
| MySQL (Jun Han)          | Browse the DB without leaving VS Code          |
| GitLens                  | Git history annotations in the gutter          |

### 8.3 Python Packages (auto-installed via `requirements.txt`)

| Package              | Role                                                  |
| -------------------- | ----------------------------------------------------- |
| `Flask`              | Web framework                                         |
| `Flask-SQLAlchemy`   | ORM integration with Flask                            |
| `Flask-Login`        | Session-based auth (login / logout / remember-me)     |
| `Flask-WTF`          | Forms + automatic CSRF protection                     |
| `WTForms`            | Form fields and validators                            |
| `PyMySQL`            | Pure-Python MySQL driver                              |
| `cryptography`       | Required by PyMySQL for `caching_sha2_password`       |
| `python-dotenv`      | Loads `.env` variables into the environment           |
| `email-validator`    | Powers `Email()` validator in WTForms                 |
| `Werkzeug`           | Password hashing (ships with Flask)                   |
| `Jinja2`             | Template engine (ships with Flask)                    |

Install them all in one go:
```powershell
pip install -r requirements.txt
```

### 8.4 Frontend Libraries (CDN — no install needed)

| Library          | Purpose                              | Source                                              |
| ---------------- | ------------------------------------ | --------------------------------------------------- |
| Bootstrap 5.3    | Grid, components, utility classes    | `cdn.jsdelivr.net/npm/bootstrap@5.3.3/.../bootstrap.min.css` |
| Bootstrap Bundle | Modals, dropdowns, tooltips (JS)     | `cdn.jsdelivr.net/npm/bootstrap@5.3.3/.../bootstrap.bundle.min.js` |

### 8.5 Coming-Later Tools (not needed for Milestone 1)

| Tool            | When you'll need it                                       |
| --------------- | --------------------------------------------------------- |
| **Pillow**      | Image resizing / compression for uploads (Milestone 2)    |
| **Flask-Mail**  | Sending notification emails (Milestone 5)                 |
| **Mailtrap**    | Catching test emails during development (Milestone 5)     |
| **Postman**     | Testing routes / future REST endpoints                    |
| **pytest**      | Automated test suite (later milestones)                   |
| **GitHub repo** | Source hosting + collaboration + final submission         |

---

## 9. Setup Guide

### 9.1 Prerequisites
See [§8.1](#81-development-software-install-once) for the full list. At minimum you need: Python 3.11+, XAMPP (for MySQL), and a code editor.

### 9.2 Install dependencies

Open PowerShell in the project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If `Activate.ps1` is blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 9.3 Create the database

Start MySQL (XAMPP Control Panel → **Start** next to MySQL). Open **phpMyAdmin** at http://localhost/phpmyadmin, click the **SQL** tab, paste the contents of [database/schema.sql](database/schema.sql), and **Go**.

### 9.4 Environment variables

Copy `.env.example` to `.env` and adjust if needed:

```
FLASK_APP=run.py
FLASK_DEBUG=1
SECRET_KEY=change-me

DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=lost_and_found

UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=3145728
```

> XAMPP's default MySQL user is `root` with **no password**.

---

## 10. Build & Run

| Task               | Command                                                   |
| ------------------ | --------------------------------------------------------- |
| Activate venv      | `.\venv\Scripts\Activate.ps1`                             |
| Run dev server     | `python run.py`                                           |
| Initialize DB      | Run `database/schema.sql` in phpMyAdmin once              |
| Install a package  | `pip install <name>` then `pip freeze > requirements.txt` |
| Run tests          | `pytest` (added in a later milestone)                     |

App serves at **http://127.0.0.1:8000**.

> Port 5000 is often reserved by Windows / Hyper-V, which throws `An attempt was made to access a socket in a way forbidden by its access permissions`. We bind to **8000** instead.

**Smoke test after setup:**
1. Visit http://127.0.0.1:8000
2. Click **Register**, create a student account
3. Log in → land on dashboard
4. Verify a row appears in the `users` table via phpMyAdmin
5. Log out, log back in

---

## 11. Project Structure

```
ite18 projcts/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # reads .env
│   ├── extensions.py        # db + login_manager singletons
│   ├── models.py            # SQLAlchemy models for the 6 ERD entities
│   ├── auth/                # blueprint: register, login, logout
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── main/                # blueprint: index, dashboard
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/           # Jinja2 + Bootstrap
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── auth/{login,register}.html
│   │   └── main/dashboard.html
│   └── static/
│       ├── css/style.css
│       └── uploads/         # item photos
├── database/
│   └── schema.sql           # MySQL DDL — run once to create tables
├── prototype.html           # ERD reference (existing)
├── chatbot_prototype.html   # chatbot reference (existing)
├── LOST-AND-FOUND.pdf       # original brief
├── ScopeProject.md          # this document
├── requirements.txt
├── .env.example
├── .gitignore
└── run.py                   # entrypoint — `python run.py`
```

---

## 12. Development Milestones

| # | Milestone               | Deliverables                                                | Status |
| - | ----------------------- | ----------------------------------------------------------- | ------ |
| 1 | Project scaffold + auth | Repo, env, DB connected, base layout, register/login/logout | done   |
| 2 | Reporting module        | Lost + Found forms, image upload, list views                | done   |
| 3 | Match engine            | Suggested matches + staff confirm/dissolve                  | done   |
| 4 | Claim workflow          | Submit claim, staff verify, status transitions              | done   |
| 5 | Notifications           | Email (Flask-Mail, optional) + in-app on match and on claim | done   |
| 6 | Dashboard & reports     | Per-role dashboard, item stats, CSV export, admin user mgmt | done   |
| 7 | ~~Chatbot integration~~ | Out of scope &mdash; the chatbot ERD is a separate concept  | skipped |
| 8 | UAT + deployment        | Bug fixes, seed demo data, deploy                           | next   |

---

## 13. Deliverables Checklist

- [ ] Source code repository
- [x] Database schema ([database/schema.sql](database/schema.sql))
- [ ] Working web app (auth, report, match, claim, notify)
- [x] [ScopeProject.md](ScopeProject.md) (this document)
- [x] [prototype.html](prototype.html) — ERD reference
- [x] [chatbot_prototype.html](chatbot_prototype.html) — chatbot reference
- [ ] User manual (1–2 pages, screenshots per role)
- [ ] Final presentation deck

---

## 14. Risks & Mitigations

| Risk                                   | Mitigation                                       |
| -------------------------------------- | ------------------------------------------------ |
| Vague item descriptions break matching | Require category + keywords; let staff override  |
| Photo storage growth                   | Compress on upload; cap file size at ~3 MB       |
| Fake claims                            | Require ID verification at staff release step    |
| Email deliverability                   | Use a transactional provider (Mailtrap → SES)    |
| Scope creep into mobile/AI             | Lock v1 scope; defer extras to v2 backlog        |
