# 🎵 MusicApp - Next-Gen Streaming & Cloud Music Vault

A full-stack, modern music streaming web application built with **Django 5**, featuring high-fidelity audio playback, YouTube smart media extraction, user upload quotas (20 free songs vs. unlimited VIP membership), custom playlists, real-time liked songs, and a dedicated administrative console.

---

## 🌟 Key Features

### 🎧 Core User Experience
- **High-Fidelity Audio & Video Player**: Persistent bottom audio dock with progress bar, volume control, shuffle, repeat (all / repeat-one), track queueing, and responsive mini/expanded YouTube video overlay.
- **Smart YouTube Media Importer**: Import songs or music videos by pasting any standard, short (`youtu.be`), YouTube Music, or Shorts link with automatic metadata and thumbnail extraction.
- **Upload Quota & Storage Vault**:
  - **Free Plan**: Upload up to 20 personal audio tracks in your private cloud vault.
  - **VIP Club Tier**: Unlimited track uploads, access to VIP-exclusive audio streams, and VIP profile badges.
  - Slot recycling: Deleting an upload instantly frees up an upload slot.
- **Privacy & Isolation**: Regular user uploads remain strictly private to the uploader, while administrator uploads populate the shared public catalog.
- **Custom Compilations**: Create, manage, and curate custom playlists with instant AJAX track addition and removal.
- **Favorites Collection**: Quick 1-click heart icon to like and curate favorite songs with instant count updates.

### 🛡️ Administrative Console
- **Dedicated Admin Control Panel (`/a/dashboard`)**:
  - Live metric aggregations: Total users, VIP subscribers, total songs, public tracks, user uploads, and VIP catalog tracks.
  - Recently added releases and most played charts.
- **Song & Media Management (`/a/songs`)**: Filter by public tracks, user uploads, VIP tracks, and media type. Full CRUD with audio/video stream replacement.
- **User Account Management (`/a/users`)**: Search users, toggle VIP subscription status with one click, modify roles, and create accounts.
- **Built-in Django Admin (`/admin`)**: Integrated with custom `CustomUserAdmin`, `SongAdmin`, `PlaylistAdmin`, and `FavoriteSongAdmin` models.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.14)
- **Virtual Environment**

### 2. Environment Setup

Clone or navigate to the repository directory:
```bash
cd django_music_app
```

Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Database Initialization
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Initial Catalog & Demo Users
Populate the database with pre-configured songs, artists, and demo user accounts:
```bash
python manage.py seed_data
```

### 5. Launch Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🔐 Default Demo Credentials

When running `seed_data`, the following pre-configured accounts are created:

| Role | Username | Password | Email | Access |
| :--- | :--- | :--- | :--- | :--- |
| **Superuser / Admin** | `admin` | `admin123` | `admin@musicapp.com` | Full Admin Console (`/a/dashboard`) & Django Admin (`/admin`) |
| **Standard User** | `user` | `user123` | `user@musicapp.com` | User App (20-song upload quota) |
| **Test User 2** | `john_doe` | `user123` | `john@musicapp.com` | User App |
| **Test User 3** | `emily_w` | `user123` | `emily@musicapp.com` | User App |

---

## 🧪 Automated Testing

MusicApp includes an exhaustive test suite covering models, forms, public views, authenticated views, upload quotas, VIP subscriptions, AJAX endpoints, admin controls, and YouTube parsing utilities.

To execute the test suite:
```bash
python manage.py test
```

### Test Coverage Highlights (60+ Automated Tests)
- ✅ **Model Logic**: VIP expiration checks, dynamic upload quota percentages, duration string formatting, file URL fallbacks.
- ✅ **Form Validation**: Duplicate username/email prevention, password confirmation, length enforcement.
- ✅ **Privacy & Isolation**: Strict partition between public songs and private user vaults.
- ✅ **Quota Enforcement**: 20-track ceiling enforcement for standard users and slot recovery on deletion.
- ✅ **VIP Subscription**: Monthly (30-day) and annual (365-day) activation, cancellation, and expiration logic.
- ✅ **AJAX Endpoints**: Safe favorite toggling, playlist CRUD, and play count logging.
- ✅ **Admin Console**: Strict RBAC permissions, self-deletion prevention, and track editing.
- ✅ **Media Utilities**: YouTube ID extraction across all standard and mobile formats.

---

## 📂 Project Architecture

```text
django_music_app/
├── manage.py                     # Django CLI utility
├── requirements.txt              # Project dependencies
├── command.txt                   # Quick command cheat sheet
├── README.md                     # Documentation
│
├── music/                        # Project configuration
│   ├── .env                      # Environment variables
│   ├── asgi.py                   # ASGI config
│   ├── settings.py               # Django settings (env-aware)
│   ├── urls.py                   # Root URL dispatcher
│   └── wsgi.py                   # WSGI config
│
├── music_player/                 # Core application
│   ├── admin.py                  # Customized Django ModelAdmin classes
│   ├── apps.py                   # App configuration
│   ├── forms.py                  # Form validation layer
│   ├── models.py                 # User, Song, Playlist, FavoriteSong models
│   ├── tests.py                  # 60+ comprehensive unit & integration tests
│   ├── urls.py                   # Application routes & AJAX endpoints
│   ├── views.py                  # Core controllers & admin handlers
│   └── management/
│       └── commands/
│           └── seed_data.py      # Database seeding command
│
├── static/                       # Static files
│   ├── css/style.css             # Glassmorphism design system & animations
│   ├── images/                   # Brand icons & default avatars
│   └── artists/                  # Default artist covers
│
├── media/                        # User and system uploaded media
│   ├── covers/                   # Song artwork & YouTube posters
│   ├── profile/                  # User profile pictures
│   └── songs/                    # Local audio tracks & downloaded streams
│
└── templates/                    # HTML Templates
    ├── 404.html                  # Custom 404 error page
    ├── 500.html                  # Custom 500 server error page
    ├── admin/                    # Administrative portal views
    │   ├── auth/                 # Admin authentication
    │   ├── layout/               # Admin master layout & sidebar
    │   ├── songs/                # Track catalog management
    │   ├── users/                # User accounts & VIP management
    │   └── videos/               # Music videos control
    └── app/                      # User-facing web application
        ├── auth/                 # Login, signup, profile & VIP upgrade
        ├── layout/               # App master layout, persistent player, sidebar
        └── songs/                # Catalog, uploads, playlists, favorites, library
```

---

## 📡 AJAX Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/toggle-favorite` | `POST` | Toggle favorite state for a given song ID (`{ song_id }`) |
| `/get-playlists` | `GET` | Retrieve logged-in user's playlists as JSON |
| `/add-to-playlist` | `POST` | Add a track to a playlist (`{ song_id, playlist_id }`) |
| `/remove-from-playlist` | `POST` | Remove a track from a playlist (`{ song_id, playlist_id }`) |
| `/create-playlist` | `POST` | Create a new playlist asynchronously (`{ name }`) |
| `/record-play` | `POST` | Increment a track's play count (`{ song_id }`) |

---

## 🔒 Security Best Practices
- **Safe Authentication**: Automatic username/email case-insensitive resolution with password hashing.
- **CSRF Protection**: All POST actions (forms and AJAX) enforce Django CSRF tokens.
- **Redirection Validation**: Login redirects validate `next` parameters to prevent open-redirect vulnerabilities.
- **Quota & Permission Enforcement**: Server-side validation ensures free users cannot bypass the 20-song limit via direct API calls.
