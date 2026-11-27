# YT-MP3: Family Playlist Maker

A web app for building a personal music library from YouTube links. Each family member signs in with Google, imports up to ten YouTube links at a time, manages their own songs, arranges them into playlists, and exports a playlist as a ZIP of numbered MP3s.

> **Status:** Milestone 4 (Export), plus a UI refresh: dark theme, account menu, skeleton loading, library paging, and pages that stay in step across tabs and browsers. Next: cleanup, a security review and deployment.
> **Version:** 0.4.0

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

- **Vue frontend:** the signed-in app (sidebar, Music Library, Import Music, Playlists, Export History) and the landing page with Google sign-in.
- **Supabase:** Google sign-in, the Postgres database, and row-level security (RLS) that keeps each user's data separate.
- **FastAPI backend:** checks links, reads video metadata with yt-dlp, writes songs to the database, and builds export ZIPs (yt-dlp + FFmpeg). It's the only part that can write songs and export records, because it holds the secret key.

Songs are stored as **links plus metadata only** (title, duration, canonical URL). Audio is only created temporarily during an export, and the ZIP is deleted shortly after.

Each user has a private library. If two users import the same YouTube video, each gets their own copy of the song record.

---

## 2. Features

### Current

- **Landing page:** a violet panel introducing Import, Playlists and Export, and a **Continue with Google** button. The background shapes drift slowly and the cards lift on hover; all motion stops when the system's "reduce motion" setting is on.
- **Google sign-in** through Supabase Auth. Each new account gets a profile automatically.
- **Music Library:** lists your songs, newest first, with:
  - Four summary cards at the top: songs, playlists using them, total length, and the last day you added songs.
  - Each song's YouTube thumbnail, title, link, length, playlists and date added.
  - 20 songs per page, with **Previous** / **Next** and "Showing 21–40 of 312" in the footer. A new search starts from page 1, and the stat cards always count the whole library.
  - Live search by title or link.
  - Select one, several, or all songs. Ticks stay when you change page; the header checkbox ticks or unticks the current page.
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
  - Lists your playlists, newest first, with the name, description, number of songs, total length, date created and when it was last exported.
  - Live search by playlist name or description.
  - Select one, several, or all playlists and delete them after a confirmation (which names the playlist when only one is selected). The songs stay in your library.
  - Each row has a ⋮ menu with **Edit playlist**, which opens the playlist, and **Export playlist**, which opens the export popup.
  - An empty state when you have no playlists.
- **Add Playlist page:** give the playlist a name (required, up to 100 characters) and an optional description (up to 500 characters, with a live counter). After saving you go straight to the new playlist so you can add songs.
- **Playlist page** (open a playlist from the list):
  - Labels under the name show the number of songs, the total length and the date created.
  - Click the name or description to edit them in a popup. Nothing is saved until you press **Save**.
  - **Add Song** opens a searchable picker with the library songs that aren't in the playlist yet, including a "Select all" box. New songs go to the end, in the order they're listed.
  - Songs are numbered in playlist order. Reorder them by dragging a row (on touch screens, press briefly first), or with **Move up** / **Move down** in the row's ⋮ menu. The new order saves automatically; if saving fails, the list goes back to the last saved order.
  - Reordering is paused while a search is active, so the numbers always match the full playlist.
  - Search within the playlist by title or link. Select songs and click **Remove Songs**, or use **Delete song** in a row's ⋮ menu. Both take the song out of this playlist straight away, with no confirmation; it stays in your library.
  - **Delete Playlist** with a confirmation.
  - **Export Playlist** opens the export popup (disabled for an empty playlist, or while another export is running).
  - A "Playlist not found" page for deleted playlists or wrong links.
- **Sidebar:** can be collapsed to icons on desktop, and becomes a slide-out menu on small screens. Your name and email at the bottom open a menu with **Log out**. The menu opens to the side when the sidebar is collapsed.
- **Logging out** shows "Logging you out…" for about a second. Supabase removes the session from the browser and revokes it on its server, then the app reloads on the landing page, so nothing from your account stays in memory and Back can't return to the app. If the session can't be removed, the app says so and you stay signed in.
- **Loading:** pages show grey placeholder shapes in the layout of the content (skeleton screens) instead of "Loading…".
- **Stays in step across tabs and browsers:** Music Library, Playlists, a playlist page and Export History update on their own when the same account changes something elsewhere. Supabase Realtime sends the change live, and the page quietly reloads its data about a second later. When a tab is shown again or its window gets focus, it also reloads, to catch anything missed while the connection was down. Reloads wait while a dialog is open, a save is running or a song is being dragged. This needs Realtime turned on for `songs`, `playlists`, `playlist_songs` and `exports` (see [Create the database](#84-create-the-database)).

- **Export Playlist:**
  - Choose **Export Playlist** on a playlist page or in a playlist's ⋮ menu, check the details, and start. Format is a ZIP of MP3s, numbered in playlist order.
  - A progress card in the bottom-right corner shows the percentage and stays visible while you move between pages. It can be collapsed and has **Cancel** and **Download** buttons. Reloading the page picks a running export back up.
  - A song that can't be downloaded is skipped, with its reason recorded; the rest are still exported. A ZIP is only offered after it is fully written and checked.
  - Limits (all configurable): up to `MAX_EXPORT_SONGS` songs per export (default 100), `DAILY_EXPORT_SONG_LIMIT` songs per rolling 24 hours (default 300), and one running export per user.
  - Missing FFmpeg, too little free disk space and a full disk are reported with a clear message.
  - Finished ZIPs stay downloadable for `EXPORT_FILE_TTL_MINUTES` (default 60), then are deleted. Temporary audio is always deleted.
- **Export History:** lists recent exports that produced a file, newest first, with the playlist name, date, song count (for example "8 of 10 · 2 skipped") and whether the ZIP is still available ("Ready until" a time, or "Expired").
  - Search by playlist name.
  - Each row has a **Download** button while the file is available. After it expires, the button becomes **Export again** if the playlist still exists.
  - Expand a row to see its songs and why any were skipped.
  - ⋮ menu: **Download** (until the file expires), **Export again**, and **Delete**.
  - **Delete History** removes every finished export. Deleting also removes the ZIP. A running export is never deleted.
  - History stores references only, so names come from your playlists and songs as they are now.

---

## 3. How It Works

```text
   Browser (Vue)                    FastAPI backend                 Supabase
+------------------+            +--------------------+         +------------------+
| Sign in (Google) |----------->|                    |         | Auth             |
| Music Library    |  token     |  check token ------+-------->| /auth/v1/user    |
| Import / Export  |----------->|  POST /imports     |         |                  |
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

### Export flow

1. You click **Export Playlist**. The browser sends your login token and the playlist ID to `POST /exports`.
2. The backend checks that the playlist is yours, the song count, the daily limit, free disk space, FFmpeg, and that you have no other export running.
3. It records an `exports` row and one `export_items` row per song, then replies `202 Accepted`.
4. In the background (a small thread pool, `MAX_CONCURRENT_EXPORTS` at a time), each song is downloaded with yt-dlp and converted to MP3 with FFmpeg, then everything is packed into a ZIP. The row's percentage is updated as it goes.
5. The browser reads the `exports` row every second to update the progress card.
6. When it finishes, **Download** asks `POST /exports/{id}/download-link` for a one-time link that works for 60 seconds. The browser downloads it like any file.
7. A background sweeper deletes ZIPs after `EXPORT_FILE_TTL_MINUTES`. If the server restarts mid-export, that export is marked failed.

### Playlist flow

Playlists don't go through the backend. The browser reads and writes them directly in Supabase, and RLS makes sure you can only touch your own playlists.

- Creating, renaming, deleting playlists and removing songs are plain table writes.
- Adding songs and reordering use two database functions, `add_songs_to_playlist` and `reorder_playlist_songs`. Each runs as one transaction, so positions stay numbered 1 to n with no gaps or duplicates.
- Reordering is optimistic: the list changes on screen at once, then one request saves it. Several quick moves are merged into a single save of the newest order.
- On the playlist page, every change to the song list (add, remove, reorder) goes through one queue, so a slow request can never overtake a newer one.
- If a save fails because the playlist was changed somewhere else, the page reloads it and says so.

### Keeping pages in step

Music Library, Playlists, a playlist page and Export History load their data once, then keep it current in two ways (`useLiveRefresh.js`):

- **Live:** each page subscribes to Supabase Realtime for the tables it shows. When one changes, the page reloads its data about 0.4 seconds later; a burst of changes causes one reload. Export progress updates are ignored, so only a new, finished or deleted export counts.
- **Catch-up:** when a tab is shown again, its window gets focus, or the live connection comes back, the page reloads. This covers changes missed while a laptop slept or the connection dropped.

Reloads are quiet: no loading placeholders, ticks are kept, and the library stays on the same page. They wait while a dialog is open, a save or delete is running, or a song is being dragged, and a hidden tab waits until it's shown.

Import and export progress still come from polling once a second (see above).

---

## 4. Technology Stack

### Frontend

Styling uses Tailwind CSS, with no component library. Notes for contributors:

- Put Tailwind classes in the template. Avoid adding `<style>` blocks unless a value can't be expressed with utilities, such as a keyframe animation.
- Colours come from the `--c-*` variables defined on `.app-shell` in `src/assets/app.css`, exposed as Tailwind colours such as `bg-surface`, `text-muted` and `border-border`. Changing a variable updates every component that uses it. A new colour gets a new `--c-*` variable and a matching `@theme inline` entry.
- The shared `app-*` classes (`app-btn`, `app-alert`, `app-card`, `app-page`, and so on) are kept as Tailwind component classes for buttons, alerts, cards and page titles.
- Tailwind's base reset (Preflight) is not enabled yet, so element defaults such as list bullets and heading margins still come from `style.css` and the browser.
- Class names are written out in full in the source, because Tailwind only generates classes it can find as complete strings.
- Animations change only `transform`, `translate`, `scale`, `rotate` or `opacity`, use CSS rather than JavaScript timers, and have `motion-reduce:` variants that stop the movement. In Tailwind v4, `translate-*` and `scale-*` set the separate `translate` and `scale` properties, so list those in `transition-[…]` or use `transition-transform`.
- Screen-size variants are `phone:` (up to 640px), `mobile:` (up to 768px) and `desktop:` (769px and up), defined in `app.css`.

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
| yt-dlp | Reads video metadata and downloads audio for exports |
| FFmpeg | Converts audio to MP3 for exports |
| Node.js | JavaScript runtime that yt-dlp uses for some YouTube lookups |
| ThreadPoolExecutor | Runs export jobs in the background |

### Data and Auth

| Technology | Purpose |
|---|---|
| Supabase Postgres | Database |
| Supabase Auth (Google OAuth) | Sign-in |
| Supabase Realtime | Tells open pages when their data changed elsewhere |
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
│   │   ├── main.py                 FastAPI app and routes (/health, /imports, /exports)
│   │   ├── auth.py                 Verifies login tokens with Supabase
│   │   ├── importer.py             Import logic: validation, quota, background work
│   │   ├── supabase_store.py       The only code that writes with the secret key
│   │   ├── config.py               Settings loaded from backend/.env
│   │   ├── errors.py               One error format for all API errors
│   │   ├── schemas.py              Request and response models
│   │   ├── youtube.py              Link validation (carried over from the POC)
│   │   ├── metadata.py             yt-dlp metadata checks (carried over from the POC)
│   │   ├── ytdlp_opts.py           yt-dlp options (carried over from the POC)
│   │   ├── names.py                Safe file names (used by export)
│   │   ├── exporter.py             Original POC exporter (kept for reference, not used)
│   │   ├── exports/                Playlist export
│   │   │   ├── service.py          Runs an export job, limits, download links, delete
│   │   │   ├── audio.py            Song -> MP3 (yt-dlp + FFmpeg)
│   │   │   ├── packager.py         MP3s -> verified ZIP
│   │   │   └── workspace.py        Temporary folders and expiry sweeper
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
│   ├── lib/
│   │   ├── supabase.js             Supabase client
│   │   └── format.js               Dates, durations, links and "3 songs"-style counts
│   ├── composables/
│   │   ├── useAuth.js              Session state and sign-in/out
│   │   ├── useSignOut.js           Log out with a short delay, then reload on the landing page
│   │   ├── useMusicLibrary.js      Loads and deletes songs
│   │   ├── useSongSearch.js        Debounced search
│   │   ├── useLiveRefresh.js       Live updates plus reload-on-return, shared by the list pages
│   │   ├── useSongSelection.js     Row selection
│   │   ├── usePagination.js        Splits a loaded list into pages of 20
│   │   ├── useImport.js            Import state and progress polling
│   │   ├── usePlaylists.js         Loads and deletes playlists
│   │   ├── usePlaylistDetail.js    One playlist: edit, add, remove, reorder
│   │   ├── useAddToPlaylist.js     Library's "Add to Playlist" popup
│   │   ├── useExportJob.js         Running export: start, progress, cancel, download
│   │   └── useSongPicker.js        Playlist page's "Add Song" popup
│   ├── services/
│   │   ├── musicLibraryService.js  Song queries (Supabase)
│   │   ├── playlistService.js      Playlist queries and writes (Supabase)
│   │   ├── playlistRules.js        Name/description limits and checks
│   │   ├── importService.js        Calls POST /imports and reads batches
│   │   ├── exportService.js        Export calls, history, download, delete
│   │   └── apiError.js             Error type for backend calls
│   ├── components/
│   │   ├── layout/                 Sidebar, account menu, app shell, log-out overlay
│   │   ├── library/                Summary cards, song table, empty state, delete dialog
│   │   ├── import/                 Links box, progress bar, results
│   │   ├── playlists/              Playlist table, song list, dialogs
│   │   ├── export/                 Export popup, progress card, delete dialog
│   │   └── ui/                     Shared dialog, page header, list card, selection bar, row menu,
│   │                               song thumbnail, progress bar, loading skeleton, pager
│   ├── views/
│   │   ├── LandingView.vue         Sign-in page
│   │   ├── MusicLibraryView.vue
│   │   ├── ImportMusicView.vue
│   │   ├── PlaylistsView.vue       List of playlists
│   │   ├── PlaylistNewView.vue     Add Playlist form
│   │   ├── PlaylistDetailView.vue  One playlist and its songs
│   │   ├── ExportHistoryView.vue   Past exports, download, delete
│   │   └── PocView.vue             Legacy, dev only, not working with the new backend
│   ├── assets/
│   │   ├── app.css                 Tailwind setup, colour tokens, animations and shared app-* classes
│   │   └── brand/                  Logo, icon and the Google "G"
│   └── style.css                   Global base styles (font, page defaults, the POC's buttons)
│
├── package.json
├── vite.config.js
└── README.md
```

Legacy files from the proof of concept are still in the repo but aren't used by the app: `src/api/`, `src/composables/useLinks.js`, `src/services/useImport.js` (an old copy of `composables/useImport.js`), the POC components directly under `src/components/` (`ImportButton.vue`, `PlaylistHistory.vue`, and so on), `src/components/icons/`, `src/components/layout/PlaceholderPage.vue`, the Vue starter files `src/assets/main.css`, `src/assets/base.css` and `src/assets/logo.svg`, and `backend/test_connection.py`. They're scheduled for removal.

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
| `exports` | One row per export: playlist, status, percent, file expiry. | Own rows | Backend only |
| `export_items` | One row per song in an export: its position, result and any skip reason. | Own rows | Backend only |

Constraints worth knowing:

- Each user can have a given video only once in `songs`.
- Each import can have 1 to 10 links.
- A user can have only one active export at a time (a partial unique index).
- Export history stores references only (which playlist, which song at which position), so names are read from `playlists` and `songs`.
- Playlist positions are unique per playlist. The check is deferred, so a reorder can swap positions inside one transaction.
- A playlist description can be at most 500 characters.
- A playlist's `updated_at` changes whenever its songs are added, removed or reordered.

**Upgrading from Milestone 3:** run section 7 of `database/schema.sql` (the `exports` and `export_items` tables) in the Supabase SQL Editor.

**Upgrading from Milestone 2:** if your database was created from the older schema, add the new column and permission before using playlists:

```sql
alter table public.playlists
    add column description text check (description is null or length(description) <= 500);
grant update (name, description) on public.playlists to authenticated;
```

The schema also defines two playlist functions the browser calls through `supabase.rpc`: `add_songs_to_playlist(p_playlist_id, p_song_ids)` appends songs to the end of a playlist, skips ones already in it, and returns how many were added; `reorder_playlist_songs(p_playlist_id, p_song_ids)` renumbers every song 1 to n in one transaction.

Only the backend holds the secret key, and only it can write songs, import rows and export rows. The browser never gets write access to those tables.

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
| FFmpeg | Needed for export. Must be on your PATH (check with `where ffmpeg`, then restart your terminal). Not needed for import. |

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
3. Turn on live updates, so open tabs and browsers stay in step. Run this once in the SQL Editor:

   ```sql
   alter publication supabase_realtime add table
     public.songs, public.playlists, public.playlist_songs, public.exports;
   ```

   If it says a table is already a member of the publication, live updates are already on for it. Row-level security still applies, so each user only receives their own new and changed rows.

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

# Export (optional; these are the defaults)
MAX_EXPORT_SONGS=100
DAILY_EXPORT_SONG_LIMIT=300
MAX_CONCURRENT_EXPORTS=2
EXPORT_FILE_TTL_MINUTES=60
EXPORT_MIN_FREE_MB=1024
# EXPORT_DIR=   (folder for temporary audio and ZIPs; defaults to the system temp folder)
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

Avoid `--reload` and multiple workers while testing. Restarting the server during an import or export marks it as failed, by design. On startup the backend warns "FFmpeg was not found" if exports can't run.

### Terminal 2: frontend

```bash
npm run dev
```

Open <http://localhost:5173> in your browser. Use `localhost` or `127.0.0.1` exactly as shown, because the backend only accepts those origins by default.

Press `Ctrl + C` in either terminal to stop it.

---

## 10. Using the Application

1. **Sign in:** click **Continue with Google**. Your profile is created on first sign-in.
2. **Music Library:** your songs appear here, with totals at the top. Use **Previous** / **Next** at the bottom to move between pages of 20 and the search box to filter. Tick songs, then click **Delete** to remove them (after a confirmation).
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
6. **Export a playlist:** open a playlist (or use its ⋮ menu in the list), click **Export Playlist**, and confirm. Watch the progress card, then click **Download** when it's ready.
7. **Export History:** download a recent export again, export the playlist again, or delete exports (one at a time or with **Delete History**).
8. **Log out:** click your name and email at the bottom of the sidebar, then choose **Log out**.

On a phone, use the menu button at the top to open the sidebar.

---

## 11. Backend API

Playlists don't use the backend; the browser talks to Supabase directly (see [Playlist flow](#playlist-flow)).

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Checks the server is running |
| POST | `/imports` | Bearer token | Starts an import and returns its batch ID |
| POST | `/exports` | Bearer token | Starts a playlist export (`{playlist_id, format: "zip"}`) and returns its export ID |
| POST | `/exports/{id}/cancel` | Bearer token | Cancels a running export |
| POST | `/exports/{id}/download-link` | Bearer token | Returns a link that works for 60 seconds (410 if the file expired) |
| GET | `/exports/download/{token}` | Link token | Downloads the ZIP |
| DELETE | `/exports/{id}` | Bearer token | Deletes one finished export and its ZIP (404 if missing, 409 if still running) |
| DELETE | `/exports` | Bearer token | Deletes all finished exports; returns `{"deleted": n}` |

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

Export progress is read from the `exports` row in Supabase, like imports. Export errors use the same error shape.

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
- Export rules: limits, ownership, skipped songs, ZIP verification, cleanup of temporary files, download links, cancel, and deleting history.
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

- **Export needs FFmpeg and the backend on your machine.** ZIPs are kept in a temporary folder and deleted after an hour.
- **Deleting export history resets the daily export count,** because that count comes from the same rows.
- **Removing songs from a playlist has no undo or confirmation.** The songs stay in the library, so they can be added back.
- **No reordering during search:** drag and Move up/down are turned off while the playlist search box has text.
- **Imports need the backend running on your machine.** There's no hosted backend yet.
- **Only one backend process is supported.** Background imports and exports, download links and the restart cleanup all assume a single process.
- **Library size:** the whole library is loaded into the browser (1,000 songs per request) and paged there, so search, the summary cards and Add to Playlist see every song. A very large library takes longer to open.
- **Live updates need Realtime turned on** (section 8.4, step 3). Without it, pages still catch up when you return to the tab, but don't update by themselves.
- **Delete notices reach every signed-in user.** Supabase can't check who owned a deleted row, so it sends the deleted row's ID (a random ID, no titles or names) to everyone watching that table. Pages ignore IDs they aren't showing, except removals from a playlist, which cause a quiet reload.
- **Daily quotas:** `DAILY_IMPORT_LIMIT` and `DAILY_EXPORT_SONG_LIMIT` are placeholder values. Set them to what you want.
- **Google consent screen:** check its publishing status in Google Cloud before sharing the app with family.
- **Legacy files:** the POC files listed in section 5 are still in the repo and aren't used.
- **Not deployed:** no production hosting or production URL yet.

---

## 14. Roadmap

1. ~~**Playlists:** create playlists, add songs, reorder, rename and delete.~~ Done in Milestone 3.
2. ~~**Export:** download a playlist as a ZIP of numbered MP3s, with an Export History page.~~ Done in Milestone 4.
3. **Cleanup:** delete the legacy POC files and the `/poc` route.
4. **Live progress:** show import and export progress through Supabase Realtime instead of polling every second. (Pages already use Realtime to stay in step.)
5. **Faster token checks:** verify login tokens locally with the project's public keys, instead of calling Supabase on each request.
6. **Frontend tests:** automated tests for the playlist and library pages.
7. **Deployment:** choose a backend host that can run yt-dlp and FFmpeg, and set the production URL in Supabase.

---

## 15. Legal and Usage Considerations

This is a personal, family-use project. You are responsible for making sure you have the rights to any media you process.

The application doesn't bypass YouTube's access controls or content protection. Review copyright law, content licenses and YouTube's Terms of Service before deploying the app or expanding it beyond personal use.