# 🚗 UniRide — University Carpooling Platform

> A full-stack carpooling web application built for Islamic University of Madinah students, connecting drivers and passengers for safe, affordable, and eco-friendly commutes.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-Template_Engine-B41717?style=flat-square)
![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-Academic-lightgrey?style=flat-square)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Database Schema](#-database-schema)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [API Routes](#-api-routes)
- [Testing](#-testing)
- [Academic Context](#-academic-context)
- [Author](#-author)

---

## 🌟 Overview

**UniRide** is a university-scoped carpooling platform that allows verified students to share rides to and from campus. Drivers post available rides; passengers discover and book seats in real time. The platform handles the full lifecycle — from registration and booking to live tracking, in-app chat, wallet payments, and emergency SOS alerts.

Built as the Phase 3 Implementation deliverable for **Software Engineering (SE-3381)**, the system implements all 14 functional requirements and 5 use cases defined in the approved Phase 1 & Phase 2 design documents.

---

## ✅ Features

### Passenger
- Register and verify a university email account
- Search rides by origin, destination, and departure date
- Book one or more seats and pay via in-app wallet
- Real-time ride tracking on an interactive map
- In-app chat with the driver
- Rate the driver after ride completion
- Trigger an SOS emergency alert during a ride

### Driver
- Register with vehicle details and driving licence
- Post one-time or recurring rides (e.g. Sun/Tue/Thu)
- Approve or reject booking requests
- Broadcast live GPS location during an active ride
- View passenger profiles and ratings
- Receive fare payments directly into wallet

### Admin
- Manage all users, rides, and bookings
- Verify driver licences
- Acknowledge and resolve SOS events
- Monitor platform activity via dashboard

---

## 🏗️ Architecture

UniRide follows a **three-tier MVC architecture** with server-side rendering via Jinja2.
┌─────────────────────────────────────────────┐
│              Presentation Layer              │
│    Jinja2 Templates + Tailwind CSS + JS      │
│    (Leaflet.js maps, Flask-SocketIO chat)    │
└─────────────────────┬───────────────────────┘
│  HTTP / WebSocket
┌─────────────────────▼───────────────────────┐
│              Application Layer               │
│     Flask Blueprints (auth, rides,           │
│     bookings, wallet, chat, sos, admin)      │
│     Flask-Login · Flask-SocketIO             │
└─────────────────────┬───────────────────────┘
│  SQLite3 (via sqlite3)
┌─────────────────────▼───────────────────────┐
│                 Data Layer                   │
│   9 normalised tables · Triggers · Indexes   │
│   SQLite3 · WAL mode · FK enforcement        │
└─────────────────────────────────────────────┘

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Framework | Flask 3.x |
| Templating | Jinja2 (server-side rendering) |
| Database | SQLite3 (3NF normalised, 9 tables) |
| Real-time | Flask-SocketIO (chat & live tracking) |
| Authentication | Flask-Login + bcrypt password hashing |
| Maps | Leaflet.js |
| Frontend | Tailwind CSS 3, Vanilla JS |
| Forms | Flask-WTF + WTForms |
| Testing | pytest + pytest-flask |

---

## 🗄️ Database Schema

The database consists of **nine 3NF-normalised tables** matching the UML Class Diagram and ERD from the approved Phase 2 design document.
users               Core user accounts (PASSENGER / DRIVER / ADMIN)
drivers             Driver extension — licence + vehicle details (JSON)
rides               Ride listings with GPS coords, seats, recurrence
bookings            Passenger seat reservations (status lifecycle)
ratings             Post-ride mutual ratings (1–5 stars)
messages            Per-ride in-app chat messages
wallet              One wallet per user, balance in SAR
wallet_transactions Immutable ledger for every financial operation
notifications       Push-style alerts for booking, chat, SOS events
sos_events          Emergency triggers with lat/lng and admin resolution

Key database behaviours enforced at the SQLite level:

- **`trg_booking_approved_decrement`** — atomically decrements `rides.available_seats` when a booking is approved; raises `ABORT` if seats are insufficient
- **`trg_booking_cancelled_restore`** — restores seats when an approved booking is cancelled or rejected
- **`trg_update_driver_stats`** — recalculates `drivers.average_rating` and `total_rides_given` after every new rating insert
- **WAL journal mode** — enabled at startup for improved concurrent read performance

---

## 📁 Project Structure
uniride/
├── app/
│   ├── init.py             # App factory, extensions init
│   ├── config.py               # Config classes (Dev/Prod/Test)
│   ├── models/                 # SQLite3 query helpers (one per table)
│   │   ├── user.py
│   │   ├── ride.py
│   │   ├── booking.py
│   │   ├── wallet.py
│   │   └── ...
│   ├── blueprints/
│   │   ├── auth/               # FR-01, FR-02 — Register, Login, Logout
│   │   ├── rides/              # FR-04 to FR-07 — Create, Search, Track
│   │   ├── bookings/           # FR-08 to FR-10 — Request, Approve, Cancel
│   │   ├── chat/               # FR-11 — SocketIO real-time messaging
│   │   ├── wallet/             # FR-12 — Top-up, payment, history
│   │   ├── ratings/            # FR-13 — Post-ride ratings
│   │   ├── sos/                # FR-14 — SOS trigger & resolution
│   │   └── admin/              # FR-14 — Admin dashboard
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── rides/
│   │   ├── bookings/
│   │   ├── wallet/
│   │   ├── chat/
│   │   └── admin/
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
├── database/
│   ├── schema.sql              # All CREATE TABLE, triggers, indexes
│   └── seed.sql                # Sample data (2 admins, 3 drivers, 3 passengers…)
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_rides.py
│   ├── test_bookings.py
│   └── test_wallet.py
├── migrations/                 # Manual SQL migration scripts
├── .env.example
├── requirements.txt
├── run.py                      # Entry point
└── README.md

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/uniride.git
cd uniride

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set SECRET_KEY, DATABASE_PATH, etc.

# 5. Initialise the database
sqlite3 uniride.db < database/schema.sql
sqlite3 uniride.db < database/seed.sql

# 6. Run the development server
python run.py
```

The app will be available at **http://127.0.0.1:5000**.

### Environment Variables

```ini
# .env.example
SECRET_KEY=your-secret-key-here
DATABASE_PATH=uniride.db
FLASK_ENV=development
FLASK_DEBUG=1
```

---

## 🧭 Usage

### Default Seed Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `sara.admin@uniride.edu.sa` | `Password@123` |
| Admin | `khalid.admin@uniride.edu.sa` | `Password@123` |
| Driver | `fahad.driver@student.university.edu.sa` | `Password@123` |
| Driver | `nawaf.driver@student.university.edu.sa` | `Password@123` |
| Driver | `reema.driver@student.university.edu.sa` | `Password@123` |
| Passenger | `aiman.passenger@student.university.edu.sa` | `Password@123` |
| Passenger | `layla.passenger@student.university.edu.sa` | `Password@123` |
| Passenger | `omar.passenger@student.university.edu.sa` | `Password@123` |

### Core Workflows

**Book a ride (passenger)**
1. Log in → Search rides by origin & destination
2. Select a ride → click **Request Booking**
3. Confirm seats and wallet payment
4. Receive notification when the driver approves

**Post a ride (driver)**
1. Log in → **My Rides** → **Create Ride**
2. Set origin, destination, departure time, seats, price
3. Toggle recurring days if needed
4. Approve or reject incoming booking requests

**Admin — resolve an SOS**
1. Log in to admin dashboard → **SOS Events**
2. Click **Acknowledge** → contact emergency services if needed
3. Click **Resolve** once the situation is handled

---

## 🗺️ API Routes

> UniRide is a server-rendered application. All routes return HTML via Jinja2 templates. SocketIO events handle real-time features.

| Blueprint | Method | Route | Description |
|---|---|---|---|
| auth | GET/POST | `/register` | User registration (FR-01) |
| auth | GET/POST | `/login` | Login (FR-02) |
| auth | GET | `/logout` | Logout |
| rides | GET | `/rides` | Search rides (FR-05) |
| rides | GET/POST | `/rides/create` | Create a new ride (FR-04) |
| rides | GET | `/rides/<id>` | Ride detail & live map (FR-06) |
| rides | POST | `/rides/<id>/cancel` | Cancel a ride |
| bookings | POST | `/bookings/request` | Request a booking (FR-08) |
| bookings | POST | `/bookings/<id>/approve` | Approve booking (FR-09) |
| bookings | POST | `/bookings/<id>/reject` | Reject booking (FR-09) |
| bookings | POST | `/bookings/<id>/cancel` | Cancel booking (FR-10) |
| chat | GET | `/chat/<ride_id>` | Chat room (FR-11) |
| wallet | GET | `/wallet` | Wallet dashboard (FR-12) |
| wallet | POST | `/wallet/topup` | Top up balance |
| ratings | POST | `/ratings/submit` | Submit a rating (FR-13) |
| sos | POST | `/sos/trigger` | Trigger SOS (FR-14) |
| admin | GET | `/admin/dashboard` | Admin overview (FR-14) |
| admin | GET | `/admin/sos` | SOS events list |

**SocketIO events**

| Event | Direction | Description |
|---|---|---|
| `join_ride` | Client → Server | Join a ride's chat/tracking room |
| `send_message` | Client → Server | Send a chat message (FR-11) |
| `new_message` | Server → Client | Broadcast new message to room |
| `location_update` | Client → Server | Driver broadcasts GPS position (FR-06) |
| `location_broadcast` | Server → Client | Push location to all passengers in room |

---

## 🧪 Testing

```bash
# Run the full test suite
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific test module
pytest tests/test_bookings.py -v
```

---

## 📚 Academic Context

| Field | Detail |
|---|---|
| Course | Software Engineering — SE-3381, Section 3423 |
| Phase | Phase 3 — Implementation |
| University | King Abdulaziz University |
| Semester | April 2026 |
| Student | AIMAN RADJI — ID 441025663 |

---

## 👤 Author

**AIMAN RADJI**    
Bachelor of Computer Science (Data Science Specialisation)  
Islamic University of Madinah

---

*Built with Flask · SQLite3 · Jinja2 · Leaflet.js · Tailwind CSS*
