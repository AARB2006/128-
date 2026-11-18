# YT-MP3: Family Playlist Maker

A web app for building a personal music library from YouTube links. Each family member signs in with Google, imports up to ten YouTube links at a time, manages their own songs, and arranges them into playlists. MP3 export is planned for the next milestone.

> **Status:** Milestone 3 (Playlists). Export is still a placeholder page.
> **Version:** 0.3.0

---

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [How It Works](#3-how-it-works)
4. [Technology Stack](#4-technology-stack)
5. [Project Structure](#5-project-structure)
6. [Database](#6-database)
7. [Prerequisites](#7-prerequisites)
8. [Installation and Configuration](#8-installation-and-configuration)
9. [Running the Application](#9-running-the-application)
10. [Using the Application](#10-using-the-application)
11. [Backend API](#11-backend-api)
12. [Testing](#12-testing)
13. [Current Limitations](#13-current-limitations)
14. [Roadmap](#14-roadmap)
15. [Legal and Usage Considerations](#15-legal-and-usage-considerations)

---

## 1. Overview

YT-MP3 is split into three parts:

- **Vue frontend:** the signed-in app (sidebar, Music Library, Import Music, Playlists, Account) and the landing page with Google sign-in.
- **Supabase:** Google sign-in, the Postgres database, and row-level security (RLS) that keeps each user's data separate.
- **FastAPI backend:** checks links, reads video metadata with yt-dlp, and writes songs to the database. It's the only part that can write songs, because it holds the secret key.

Songs are stored as **links plus metadata only** (title, duration, canonical URL). No audio is stored.

Each user has a private library. If two users import the same YouTube video, each gets their own copy of the song record.

---

## 2. Features

### Current

- **Google sign-in** through Supabase Auth. Each new account gets a profile automatically.
- **Music Library:** lists your songs, newest first, with:
  - Live search by title or link.
  - Select one, several, or all songs.
  - Delete with a confirmation dialog. Deleting a song also removes it from your own playlists.
  - A **Playlists** column showing how many playlists each song is in. Click it for a popup listing those playlists, each linking to its page.
  - **Add to Playlist:** pick one of your playlists (shown with their song counts) for the selected songs. Songs are added in library order, songs already in that playlist are skipped, and a message says how many were added. If you have no playlists yet, the popup links to Add Playlist.
  - An empty state for new accounts.
- **Import Music:**
  - Paste up to 10 YouTube links, one per line. Blank lines are ignored.
  - Accepted formats: `youtube.com/watch?v=` (also `www.`, `m.` and `music.`), `youtu.be/`, `/shorts/`, `/embed/`, `/live/`, `/v/`, and `youtube-nocookie.com/embed/`. Links pasted without `https://` are accepted too.
  - Videos are rejected if they're private, members-only, Premium-only, age-restricted, live or upcoming, or longer than `MAX_VIDEO_SECONDS` (default 30 minutes).
  - Each link is checked on its own. A bad link doesn't cancel the others.
  - An animated progress bar shows "Importing Music 2/3..." while the import runs.
  - When it finishes, you see a summary: songs added, duplicates skipped, and each failed link with its reason. Failed links go back in the box so you can fix them and retry.
  - Reloading the page, or opening it on another device, picks the running import back up.
  - Daily quota per user (default 100 links per rolling 24 hours), set by `DAILY_IMPORT_LIMIT`.
  - Only one import can run at a time per user.
- **Playlists page:**
  - Lists your playlists, newest first, with the name, description, date created and number of songs.
  - Live search by playlist name or description.
  - Select one, several, or all playlists and delete them after a confirmation (which names the playlist when only one is selected). The songs stay in your library.
  - Each row has a ⋮ menu with **Edit playlist**, which opens the playlist, and **Export playlist**, which is disabled until export is built.
  - An empty state when you have no playlists.
- **Add Playlist page:** give the playlist a name (required, up to 100 characters) and an optional description (up to 500 characters, with a live counter). After saving you go straight to the new playlist so you can add songs.
- **Playlist page** (open a playlist from the list):
  - Click the name or description to edit them in a popup. Nothing is saved until you press **Save**.
  - **Add Song** opens a searchable picker with the library songs that aren't in the playlist yet, including a "Select all" box. New songs go to the end, in the order they're listed.
  - Songs are numbered in playlist order. Reorder them by dragging a row (on touch screens, press briefly first), or with **Move up** / **Move down** in the row's ⋮ menu. The new order saves automatically; if saving fails, the list goes back to the last saved order.
  - Reordering is paused while a search is active, so the numbers always match the full playlist.
  - Search within the playlist by title or link. Select songs and click **Remove Songs**, or use **Delete song** in a row's ⋮ menu. Both take the song out of this playlist straight away, with no confirmation; it stays in your library.
  - **Delete Playlist** with a confirmation.
  - **Export Playlist** is shown but disabled until export is built.
  - A "Playlist not found" page for deleted playlists or wrong links.
- **Account:** shows your name and email from your profile. In development mode it also shows a data-separation check that should report exactly 1 visible profile.
- **Sidebar:** can be collapsed to icons on desktop, and becomes a slide-out menu on small screens.

### Coming in Later Milestones

- **Export Music:** download a playlist as numbered MP3s in a ZIP file. The page is a placeholder for now.

---

## 3. How It Works

```text
   Browser (Vue)                    FastAPI backend                 Supabase
+------------------+            +--------------------+         +------------------+
| Sign in (Google) |----------->|                    |         | Auth             |
| Music Library    |  token     |  check token ------+-------->| /auth/v1/user    |
| Import Music     |----------->|  POST /imports     |         |                  |
|                  |  links     |   |                |         | Postgres + RLS   |
| polls progress   |<-----------+---+ background job |-------->| songs, batches,  |
| (reads rows) ----+------------+-------------------------------->| import_items     |
+------------------+  own rows  |  yt-dlp (metadata) |         +------------------+
                                +--------------------+
```

### Import flow

1. You paste links and click **Import**. The browser sends your login token and the links to `POST /imports`.
2. The backend asks Supabase who the token belongs to. It never trusts a user ID sent in the request body.
3. The backend checks the link count, the daily quota, and whether an import is already running.
4. It records a batch and one row per link, then replies `202 Accepted` with the batch ID.
5. In the background, it fetches each link's metadata and saves the song. It updates that link's row as it goes.
6. The browser reads the batch every second, showing the link currently in progress and the overall percentage.

### Why the progress comes from the database

Each link's result is written to the database as soon as it's known. Because of that, a reload or a second device can show the same progress without any extra state in the backend.

### Playlist flow

Playlists don't go through the backend. The browser reads and writes them directly in Supabase, and RLS makes sure you can only touch your own playlists.

- Creating, renaming, deleting playlists and removing songs are plain table writes.
- Adding songs and reordering use two database functions, `add_songs_to_playlist` and `reorder_playlist_songs`. Each runs as one transaction, so positions stay numbered 1 to n with no gaps or duplicates.
- Reordering is optimistic: the list changes on screen at once, then one request saves it. Several quick moves are merged into a single save of the newest order.
- On the playlist page, every change to the song list (add, remove, reorder) goes through one queue, so a slow request can never overtake a newer one.
- If a save fails because the playlist was changed somewhere else, the page reloads it and says so.

---

## 4. Technology Stack

### Frontend

Styling uses Tailwind CSS, with no component library. Notes for contributors:

- Put Tailwind classes in the template. Avoid adding `<style>` blocks unless a value can't be expressed with utilities, such as a keyframe animation.
- Colours come from the `--c-*` variables defined on `.app-shell` in `src/assets/app.css`, exposed as Tailwind colours such as `bg-surface`, `text-muted` and `border-border`. Changing a variable updates every component that uses it. A new colour gets a new `--c-*` variable and a matching `@theme inline` entry.
- The shared `app-*` classes (`app-btn`, `app-alert`, `app-card`, `app-page`, and so on) are kept as Tailwind component classes for buttons, alerts, cards and page titles.
- Tailwind's base reset (Preflight) is not enabled yet, so element defaults such as list bullets and heading margins still come from `style.css` and the browser.
- Class names are written out in full in the source, because Tailwind only generates classes it can find as complete strings.

| Technology | Purpose |
|---|---|
| Vue 3 (`<script setup>`) | UI framework |
| Vue Router 4 | Routing and the sign-in route guard |
| Vite 8 | Development server and build |
| supabase-js v2 | Google sign-in, reading data and writing playlists under RLS |
| vue-draggable-plus | Drag-and-drop reordering of playlist songs |
| Tailwind CSS 4 (`@tailwindcss/vite`) | Styling: utility classes in the templates, with the app's colours as theme tokens |

### Backend

| Technology | Purpose |
|---|---|
| Python | Backend language |
| FastAPI | REST API |
| Uvicorn | ASGI server |
| Pydantic | Request validation |
| httpx | Calls to Supabase Auth and the Supabase REST API |
| python-dotenv | Loads `backend/.env` |
| yt-dlp | Reads video metadata |
| Node.js | JavaScript runtime that yt-dlp uses for some YouTube lookups |

### Data and Auth

| Technology | Purpose |
|---|---|
| Supabase Postgres | Database |
| Supabase Auth (Google OAuth) | Sign-in |
| Row-level security | Keeps each user's rows private |

### Testing

| Technology | Purpose |
|---|---|
| pytest | Backend tests |
| `npm run build` | Frontend compile check |

---

## 5. Project Structure

```text
128-/
├── database/
│   └── schema.sql                  Full database schema, RLS and triggers
│
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI app and routes (/health, /imports)
│   │   ├── auth.py                 Verifies login tokens with Supabase
│   │   ├── importer.py             Import logic: validation, quota, background work
│   │   ├── supabase_store.py       The only code that writes with the secret key
│   │   ├── config.py               Settings loaded from backend/.env
│   │   ├── errors.py               One error format for all API errors
│   │   ├── schemas.py              Request and response models
│   │   ├── youtube.py              Link validation (carried over from the POC)
│   │   ├── metadata.py             yt-dlp metadata checks (carried over from the POC)
│   │   ├── ytdlp_opts.py           yt-dlp options (carried over from the POC)
│   │   ├── names.py                Safe file names (kept for export)
│   │   ├── exporter.py             MP3/ZIP export (kept, not wired up yet)
│   │   ├── database.py             Legacy MySQL code, not used
│   │   └── models.py               Legacy MySQL models, not used
│   ├── tests/                      pytest suite
│   ├── .env.example                Template for backend/.env
│   └── requirements.txt
│
├── src/
│   ├── main.js                     App entry point
│   ├── App.vue                     Root component (redirects on sign-out)
│   ├── router/index.js             Routes and the sign-in guard
│   ├── lib/supabase.js             Supabase client
│   ├── composables/
│   │   ├── useAuth.js              Session state and sign-in/out
│   │   ├── useMusicLibrary.js      Loads and deletes songs
│   │   ├── useSongSearch.js        Debounced search
│   │   ├── useSongSelection.js     Row selection
│   │   ├── useImport.js            Import state and progress polling
│   │   ├── usePlaylists.js         Loads and deletes playlists
│   │   ├── usePlaylistDetail.js    One playlist: edit, add, remove, reorder
│   │   ├── useAddToPlaylist.js     Library's "Add to Playlist" popup
│   │   └── useSongPicker.js        Playlist page's "Add Song" popup
│   ├── services/
│   │   ├── musicLibraryService.js  Song queries (Supabase)
│   │   ├── playlistService.js      Playlist queries and writes (Supabase)
│   │   ├── playlistRules.js        Name/description limits and checks
│   │   ├── importService.js        Calls POST /imports and reads batches
│   │   └── apiError.js             Error type for backend calls
│   ├── components/
│   │   ├── layout/                 Sidebar, app shell, placeholder page
│   │   ├── library/                Toolbar, song table, delete dialog
│   │   ├── import/                 Links box, progress bar, results
│   │   ├── playlists/              Playlist table, song list, dialogs
│   │   └── ui/                     Shared dialog, page toolbar, row menu
│   ├── views/
│   │   ├── LandingView.vue         Sign-in page
│   │   ├── MusicLibraryView.vue
│   │   ├── ImportMusicView.vue
│   │   ├── PlaylistsView.vue       List of playlists
│   │   ├── PlaylistNewView.vue     Add Playlist form
│   │   ├── PlaylistDetailView.vue  One playlist and its songs
│   │   ├── ExportMusicView.vue     Placeholder
│   │   ├── AccountView.vue
│   │   └── PocView.vue             Legacy, dev only, not working with the new backend
│   ├── assets/
│   │   └── app.css                 Tailwind setup, colour tokens and shared app-* classes
│   └── style.css                   Global base styles (font, landing page button)
│
├── package.json
├── vite.config.js
└── README.md
```

Legacy files from the proof of concept are still in the repo but aren't used by the app: `src/api/`, `src/composables/useLinks.js`, `src/services/useImport.js` (an old copy of `composables/useImport.js`), the POC components directly under `src/components/` (`ImportButton.vue`, `PlaylistHistory.vue`, and so on), `src/components/icons/`, and `backend/test_connection.py`. They're scheduled for removal.

---

## 6. Database

The schema is in `database/schema.sql`. It creates these tables. Every table has RLS turned on.

| Table | Purpose | Who can read | Who can write |
|---|---|---|---|
| `profiles` | One row per user (name, email). Created automatically at first sign-in. | Own row | Own display name |
| `songs` | Your songs: link, title, duration. One copy per user per video. | Own rows | Backend only (delete: own rows) |
| `playlists` | Playlists: name and optional description. Private to the user who created them. | Own rows | Own rows (update: name and description only) |
| `playlist_songs` | Which songs are in which playlist, and in what order. | Own playlists | Own playlists (update: position only) |
| `import_batches` | One row per import: status and link count. | Own rows | Backend only |
| `import_items` | One row per link in an import: its result and any error. | Own rows | Backend only |

Constraints worth knowing:

- Each user can have a given video only once in `songs`.
- Each import can have 1 to 10 links.
- Playlist positions are unique per playlist. The check is deferred, so a reorder can swap positions inside one transaction.
- A playlist description can be at most 500 characters.
- A playlist's `updated_at` changes whenever its songs are added, removed or reordered.

The app also calls two database functions (RPCs). **They are not in `database/schema.sql` yet**, so a database built only from that file can't add songs to playlists or reorder them until they're created:

| Function | Purpose |
|---|---|
| `add_songs_to_playlist(p_playlist_id, p_song_ids)` | Appends songs to the end of a playlist, skips ones already in it, and returns how many were added. |
| `reorder_playlist_songs(p_playlist_id, p_song_ids)` | Takes every song in the playlist in its new order and renumbers them 1 to n in one transaction. |

**Upgrading from Milestone 2:** if your database was created from the older schema, add the new column and permission before using playlists:

```sql
alter table public.playlists
    add column description text check (description is null or length(description) <= 500);
grant update (name, description) on public.playlists to authenticated;
```

Only the backend holds the secret key, and only it can write songs and import rows. The browser never gets write access to those tables.

---

## 7. Prerequisites

| Requirement | Notes |
|---|---|
| Node.js | `^22.18.0` or `>=24.12.0` (set in `package.json`) |
| npm | Comes with Node.js |
| Python | 3.13 (the version used for testing) |
| pip | Comes with Python |
| Git | To clone the repository |
| Supabase account | Free tier is enough |
| Google Cloud project | Needed to create the Google OAuth client for sign-in |
| FFmpeg | Not needed for import. Needed for export when it's built. |

---

## 8. Installation and Configuration

### 8.1 Clone the repository

```bash
git clone https://github.com/AARB2006/128-.git
cd 128-
```

### 8.2 Create the Supabase project

1. Go to <https://supabase.com>, create a project, and note the **Project URL**.
2. In **Settings → API Keys**, copy:
   - the **Publishable key** (`sb_publishable_...`), which is safe to use in the browser;
   - the **Secret key** (`sb_secret_...`), which must stay on the backend.

### 8.3 Set up Google sign-in

1. **Google Cloud Console:** under **APIs & Services → Credentials**, create an **OAuth client ID** of type **Web application**. Under **Authorized redirect URIs**, add the callback URL shown on Supabase's Google provider page. It looks like `https://YOUR-PROJECT-REF.supabase.co/auth/v1/callback`.
2. **Supabase:** go to **Authentication → Providers → Google**, turn it on, and paste the Google **Client ID** and **Client secret**. Save.
3. **Supabase:** go to **Authentication → URL Configuration → Redirect URLs** and add:
   ```text
   http://localhost:5173/**
   ```
   Add your production URL here too when you deploy.

### 8.4 Create the database

1. In Supabase, open **SQL Editor**, paste the whole contents of `database/schema.sql`, and run it.
2. Run it once on a new project. If you get an error saying a trigger or table already exists, the schema is already there.

### 8.5 Configure the frontend

Create a file named `.env.local` in the **repo root** (next to `package.json`) with these values:

```env
VITE_SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxxxxxxxxxxxxxxx

# Optional: where the backend runs. This is the default.
VITE_API_BASE_URL=http://127.0.0.1:8000
```

These values are public by design. Access control comes from RLS.

Install the frontend packages from the repo root:

```bash
npm install
```

### 8.6 Configure and install the backend

Create the virtual environment from the `backend` folder:

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

On Mac or Linux, use `source .venv/bin/activate` instead of the activate line.

Create `backend/.env` by copying `backend/.env.example`. Then fill in the Supabase values:

```env
SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxxxxxxxxxxxxxxx
SUPABASE_SECRET_KEY=sb_secret_xxxxxxxxxxxxxxxx

MAX_VIDEO_SECONDS=1800
DAILY_IMPORT_LIMIT=100
JS_RUNTIME=node

ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Important:

- `SUPABASE_SECRET_KEY` bypasses row-level security. Keep it only in `backend/.env`.
- Never put the secret key in `.env.local`, in any `VITE_` variable, or in chat.
- `.env` and `.env.local` are git-ignored. Don't remove that rule.
- The backend reads `.env` only when it starts. Restart it after any change.

---

## 9. Running the Application

Run the backend and frontend in two separate terminals.

### Terminal 1: backend

```cmd
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check it's running by opening <http://127.0.0.1:8000/health>. It should show `{"status":"ok"}`.

Avoid `--reload` while testing imports. Restarting the server during an import marks that import as failed, by design.

### Terminal 2: frontend

```bash
npm run dev
```

Open <http://localhost:5173> in your browser. Use `localhost` or `127.0.0.1` exactly as shown, because the backend only accepts those origins by default.

Press `Ctrl + C` in either terminal to stop it.

---

## 10. Using the Application

1. **Sign in:** click **Continue with Google**. Your profile is created on first sign-in.
2. **Music Library:** your songs appear here. Use the search box to filter, tick songs to select them, and click **Delete Music** to remove them (after a confirmation).
3. **Import Music:** click **Import Music**, paste up to 10 YouTube links (one per line), and click **Import**.
   - The bar shows progress. When it finishes, the summary shows what was added and what failed.
   - Failed links stay in the box. Fix them and import again.
   - Duplicates (songs you already have, or repeated links) are skipped.
4. **Add songs to a playlist from the library:** tick songs in **Music Library** and click **Add to Playlist**, then choose the playlist.
5. **Playlists:**
   - Click **Add Playlist**, enter a name (and a description if you like), and save.
   - Click a playlist's name to open it. Use **Add Song** to pick songs from your library.
   - Drag rows, or use **Move up** / **Move down** in the row menu, to change the order. It saves on its own.
   - Click the name or description at the top to edit it.
   - Tick songs and click **Remove Songs** (or use **Delete song** in a row's ⋮ menu) to take them out of the playlist, or click **Delete Playlist** to delete the whole playlist. Your library isn't affected either way.
6. **Export Music:** placeholder page for now.
7. **Account:** shows your name and email.
8. **Log Out:** at the bottom of the sidebar.

On a phone, use the menu button at the top to open the sidebar.

---

## 11. Backend API

The backend exposes two endpoints. Playlists don't use the backend; the browser talks to Supabase directly (see [Playlist flow](#playlist-flow)).

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Checks the server is running |
| POST | `/imports` | Bearer token | Starts an import and returns its batch ID |

### `POST /imports`

Headers:

```http
Authorization: Bearer <your Supabase access token>
Content-Type: application/json
```

Body:

```json
{
  "urls": [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/9bZkp7q19f0"
  ]
}
```

Successful response (`202 Accepted`):

```json
{
  "batch_id": "5b1d2c3e-...",
  "total_links": 2
}
```

The import runs in the background. Progress is read from Supabase, not from this endpoint.

Possible errors. All use the same shape: `{"detail": {"message": "...", "problems": []}}`.

| Status | When |
|---|---|
| 401 | Missing, invalid or expired token |
| 409 | Another import is still running |
| 422 | No links, or more than 10 |
| 429 | Daily quota reached |
| 503 | Backend not configured, or Supabase unreachable |

The interactive API docs are at <http://127.0.0.1:8000/docs>.

The POC endpoints (`GET /playlists`, `POST /playlists`, `POST /playlists/{id}/export`) were removed in this version.

---

## 12. Testing

### Backend

From the `backend` folder, with the virtual environment active:

```bash
python -m pytest tests -q
```

The suite covers:

- Import rules: blank lines, the 10-link limit, duplicates, the daily quota, and the one-import-at-a-time rule.
- Partial failure: one bad video doesn't cancel the others, and the batch is marked `partial`.
- Supabase calls: the secret key is sent only in the `apikey` header, and the batch is closed even if Supabase fails midway.
- Authentication: missing, rejected and unreachable token checks.
- The URL validator from the POC.

These tests use fake Supabase and yt-dlp stand-ins, so they run without internet access.

`backend/test_youtube_metadata.py` is a manual script, not part of the suite. It calls YouTube, so it needs internet access.

### Frontend

From the repo root:

```bash
npm run build
```

This checks that the app compiles. There are no automated frontend tests yet, so playlist features are checked by hand.

---

## 13. Current Limitations

- **Playlist database functions are missing from the schema file.** `add_songs_to_playlist` and `reorder_playlist_songs` must be added to `database/schema.sql` (see section 6).
- **Export is not built yet.** The Export Music page is a placeholder, and the Export Playlist buttons are disabled.
- **Removing songs from a playlist has no undo or confirmation.** The songs stay in the library, so they can be added back.
- **No reordering during search:** drag and Move up/down are turned off while the playlist search box has text.
- **Export isn't wired up.** `exporter.py` is kept for later, but no route calls it.
- **Imports need the backend running on your machine.** There's no hosted backend yet.
- **Only one backend process is supported.** The background import and the restart cleanup both assume a single process.
- **Library size:** Supabase returns at most 1,000 rows per request by default. Pagination is needed before a library gets that big.
- **Daily quota:** `DAILY_IMPORT_LIMIT` is a placeholder value. Set it to what you want.
- **Google consent screen:** check its publishing status in Google Cloud before sharing the app with family.
- **Legacy files:** the POC files listed in section 5 are still in the repo and aren't used.
- **Not deployed:** no production hosting or production URL yet.

---

## 14. Roadmap

1. ~~**Playlists:** create playlists, add songs, reorder, rename and delete.~~ Done in Milestone 3.
2. **Export:** a backend endpoint that downloads the audio with yt-dlp, converts it with FFmpeg, and returns a ZIP of numbered MP3s in playlist order. Enables the Export Playlist buttons.
3. **Cleanup:** delete the legacy POC files and the `/poc` route.
4. **Live progress:** replace polling with Supabase Realtime.
5. **Faster token checks:** verify login tokens locally with the project's public keys, instead of calling Supabase on each request.
6. **Frontend tests:** automated tests for the playlist and library pages.
7. **Deployment:** choose a backend host that can run yt-dlp and FFmpeg, and set the production URL in Supabase.

---

## 15. Legal and Usage Considerations

This is a personal, family-use project. You are responsible for making sure you have the rights to any media you process.

The application doesn't bypass YouTube's access controls or content protection. Review copyright law, content licenses and YouTube's Terms of Service before deploying the app or expanding it beyond personal use.