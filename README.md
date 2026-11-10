
# YT-MP3: Family Playlist Maker

A local proof-of-concept application for creating music playlists from individual YouTube video links, storing playlist information in a MySQL database, and exporting authorized audio as MP3 files packaged in a ZIP archive.

> **Project Status:** Proof of Concept (POC) / Beta  
> **Version:** 0.1.0  
> **Purpose:** Demonstrate the feasibility of the proposed technology stack and core application workflow.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Objectives](#2-objectives)
- [3. Features](#3-features)
- [4. Technology Stack](#4-technology-stack)
- [5. System Architecture](#5-system-architecture)
- [6. Project Structure](#6-project-structure)
- [7. Database Design](#7-database-design)
- [8. Requirements and Prerequisites](#8-requirements-and-prerequisites)
- [9. Installation and Configuration](#9-installation-and-configuration)
- [10. Running the Application](#10-running-the-application)
- [11. Using the Application](#11-using-the-application)
- [12. API Endpoints](#12-api-endpoints)
- [13. Testing](#13-testing)
- [14. Current Limitations](#14-current-limitations)
- [15. Future Development](#15-future-development)
- [16. Legal and Usage Considerations](#16-legal-and-usage-considerations)

---

## 1. Project Overview

YT-MP3: Family Playlist Maker is a web-based proof of concept that demonstrates a workflow for creating playlists from individual YouTube video links and exporting their audio as MP3 files.

The application allows users to provide a playlist name and submit up to ten YouTube video links per import. The backend validates the submitted links, retrieves video metadata, and stores playlist information in a MySQL database.

Users can view previously created playlists, select a playlist, and export its tracks as individual MP3 files packaged into a ZIP archive.

The prototype uses a Vue-based frontend and a Python FastAPI backend. It is intended to serve as a functional blueprint for the development of a more complete family playlist management system.

### Project Scope

This implementation focuses on demonstrating the feasibility of the following workflow:

1. Accept YouTube video links from the user.
2. Validate the submitted links.
3. Retrieve video metadata.
4. Create and store playlists in a database.
5. Retrieve and display saved playlists.
6. Download authorized audio and convert it into MP3 format.
7. Package the resulting MP3 files into a ZIP archive.
8. Provide the ZIP archive to the user.

The current implementation prioritizes core functionality and simplicity over production-level infrastructure.

---

## 2. Objectives

The primary objectives of this proof of concept are:

- Demonstrate the integration of a Vue frontend with a Python FastAPI backend.
- Implement validation of individual YouTube video URLs.
- Retrieve video metadata using yt-dlp.
- Store playlists, songs, and playlist associations in MySQL.
- Preserve the ordering of tracks within each playlist.
- Reuse song records when the same YouTube video appears in multiple playlists.
- Convert authorized audio into MP3 format using FFmpeg.
- Generate ZIP archives containing the exported playlist tracks.
- Establish a functional foundation for future system development.

---

## 3. Features

### 3.1 Playlist Creation

- Users can provide a custom playlist name.
- Each successful import creates a new playlist record.
- Playlist names do not need to be unique.
- Each import accepts up to ten non-empty YouTube video links.
- Blank lines are ignored.
- Track ordering follows the order of submitted links.

### 3.2 YouTube URL Validation

The backend validates submitted URLs before attempting metadata extraction.

Supported URL formats include:

- Standard YouTube video URLs:
  - `youtube.com/watch?v=VIDEO_ID`
- Shortened URLs:
  - `youtu.be/VIDEO_ID`
- YouTube Shorts:
  - `youtube.com/shorts/VIDEO_ID`
- Embedded videos:
  - `youtube.com/embed/VIDEO_ID`
- YouTube Live video URLs:
  - `youtube.com/live/VIDEO_ID`
- YouTube Music video URLs:
  - `music.youtube.com/watch?v=VIDEO_ID`

The validator also supports HTTP/HTTPS links and canonicalizes accepted links into standard YouTube watch URLs.

Non-YouTube links, malformed video IDs, unsupported paths, and playlist-only URLs are rejected.

### 3.3 Video Metadata Retrieval

The application uses yt-dlp to retrieve video metadata.

Information stored includes:

- YouTube video ID
- Video title
- Canonical source URL
- Video duration

The backend verifies that the retrieved video ID matches the submitted URL.

Videos that cannot be verified or that fail the application's availability and duration checks are rejected.

### 3.4 Playlist History

- Previously created playlists are retrieved from MySQL.
- Each playlist displays its name and track count.
- Tracks are displayed in their original playlist order.
- Multiple playlists can contain the same video.
- Playlist history persists between application sessions.

### 3.5 MP3 Conversion and ZIP Export

Users can select a saved playlist and export its tracks.

The export process:

1. Retrieves the selected playlist and its tracks.
2. Downloads authorized audio using yt-dlp.
3. Converts the audio into MP3 format using FFmpeg.
4. Assigns numbered filenames based on playlist order.
5. Packages the MP3 files into a ZIP archive.
6. Sends the archive to the browser for download.
7. Cleans up temporary export files after the response is completed.

The exported archive uses the following naming convention:

```text
PlaylistName.zip
```

Example archive contents:

```text
Family Favorites.zip
├── 01 - Track One.mp3
├── 02 - Track Two.mp3
└── 03 - Track Three.mp3
```

### 3.6 Export Status Indicator

The frontend displays an animated, indeterminate progress indicator while the backend processes an export.

The indicator communicates that the export is ongoing. It does not represent an exact percentage of completion.

---

## 4. Technology Stack

### Frontend

| Technology | Purpose |
|---|---|
| Vue 3 | Frontend framework |
| JavaScript | Frontend application logic |
| Vite | Development server and build tool |
| HTML | Application structure |
| CSS | Application styling |
| Fetch API | Communication with the backend |

### Backend

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| SQLAlchemy | Object-relational mapping |
| PyMySQL | MySQL database driver |
| Pydantic | Request and response validation |
| python-dotenv | Environment variable configuration |
| yt-dlp | YouTube metadata retrieval and authorized media downloading |
| FFmpeg | Audio extraction and MP3 conversion |

### Database

| Technology | Purpose |
|---|---|
| MySQL Server 8.0 | Relational database |
| MySQL Workbench | Database administration and query execution |

### Testing

| Technology | Purpose |
|---|---|
| pytest | Backend unit testing |
| httpx | HTTP client dependency for API testing |

---

## 5. System Architecture

The application follows a simple frontend-backend architecture.

```text
+---------------------------------------+
|             Vue Frontend              |
|                                       |
|  - Playlist Name Input                |
|  - YouTube Link Input                 |
|  - Import Button                      |
|  - Playlist History                   |
|  - Playlist Selector                  |
|  - Export Button                      |
|  - Export Status Indicator            |
+-------------------+-------------------+
                    |
                    | HTTP Requests
                    | JSON / ZIP Response
                    v
+---------------------------------------+
|             FastAPI Backend           |
|                                       |
|  - Request Validation                 |
|  - YouTube URL Validation             |
|  - Metadata Retrieval                 |
|  - Playlist Management                |
|  - Database Operations                |
|  - Export Processing                  |
+----------+----------------------------+
           |
           +----------------------+
           |                      |
           v                      v
+----------------------+  +----------------------+
|     MySQL Database   |  |   yt-dlp + FFmpeg    |
|                      |  |                      |
| - Playlists          |  | - Metadata Retrieval |
| - Songs              |  | - Audio Download     |
| - Playlist Songs     |  | - MP3 Conversion     |
+----------------------+  +----------+-----------+
                                    |
                                    v
                           +------------------+
                           |    ZIP Archive   |
                           +------------------+
                                    |
                                    v
                           +------------------+
                           | Browser Download |
                           +------------------+
```

### Import Workflow

1. The user enters a playlist name and YouTube video links.
2. Vue sends an HTTP POST request to FastAPI.
3. FastAPI validates the playlist name and submitted links.
4. The backend checks for duplicate video IDs within the submission.
5. yt-dlp retrieves and verifies metadata for each unique video.
6. If verification succeeds for every submitted video, the backend begins a database transaction.
7. The playlist, required song records, and playlist-song associations are saved.
8. FastAPI returns the import result.
9. Vue retrieves the updated playlist history and displays the new playlist.

The database transaction ensures that failed imports do not leave partially created playlists or associations.

### Export Workflow

1. The user selects a saved playlist.
2. Vue sends its playlist ID to FastAPI.
3. FastAPI retrieves the playlist and its associated tracks from MySQL.
4. yt-dlp downloads the authorized audio for each track.
5. FFmpeg converts the downloaded audio into MP3 format.
6. The backend creates a ZIP archive containing the numbered MP3 files.
7. FastAPI returns the ZIP archive as a file response.
8. The browser downloads the archive.
9. Temporary export files are cleaned up after the response is sent.

---

## 6. Project Structure

The project is organized into frontend, backend, and database directories.

```text
128-ytmp3/
│
├── src/
│   ├── api/
│   │   ├── errors.js
│   │   ├── httpApi.js
│   │   ├── index.js
│   │   └── mockApi.js
│   │
│   ├── components/
│   │   ├── ExportButton.vue
│   │   ├── ImportButton.vue
│   │   ├── ImportError.vue
│   │   ├── ImportStatus.vue
│   │   ├── LinkTextbox.vue
│   │   ├── PlaylistHistory.vue
│   │   └── PlaylistNameInput.vue
│   │
│   ├── composables/
│   │   └── useLinks.js
│   │
│   └── App.vue
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── youtube.py
│   │   ├── metadata.py
│   │   ├── ytdlp_opts.py
│   │   ├── names.py
│   │   └── exporter.py
│   │
│   ├── tests/
│   │   └── test_youtube.py
│   │
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── test_youtube_metadata.py
│
├── database/
│   └── schema.sql
│
├── public/
├── package.json
├── package-lock.json
├── vite.config.js
├── index.html
├── .gitignore
└── README.md
```

**Note:** The `.env` file and virtual environment are local configuration files and should not be committed to the repository. The `mockApi.js` file is retained as a reference implementation; the active frontend API uses `httpApi.js`.

---

## 7. Database Design

The prototype uses three relational tables.

### 7.1 `playlists`

Stores playlist information.

| Column | Description |
|---|---|
| `playlist_id` | Primary key |
| `name` | Playlist name |
| `created_at` | Playlist creation timestamp |

### 7.2 `songs`

Stores unique YouTube video information.

| Column | Description |
|---|---|
| `song_id` | Primary key |
| `video_id` | Unique YouTube video ID |
| `source_url` | Canonical YouTube URL |
| `title` | Video title |
| `duration_seconds` | Video duration |
| `date_added` | Record creation timestamp |

The `video_id` column is unique, allowing the same song record to be reused across multiple playlists.

### 7.3 `playlist_songs`

Associates songs with playlists and preserves their ordering.

| Column | Description |
|---|---|
| `playlist_song_id` | Primary key |
| `playlist_id` | Foreign key referencing `playlists` |
| `song_id` | Foreign key referencing `songs` |
| `position` | Track position within the playlist |
| `added_at` | Association creation timestamp |

### Relationships

```text
playlists 1 -------- M playlist_songs M -------- 1 songs
```

This structure allows:

- One playlist to contain multiple songs.
- One song to belong to multiple playlists.
- The same video to be reused without creating duplicate song records.
- Each playlist to maintain its own track ordering.

### Database Creation

Create the database using MySQL Workbench:

```sql
CREATE DATABASE ytmp3_beta
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

After creating the database, execute the SQL statements in:

```text
database/schema.sql
```

This creates the required tables and relationships.

---

## 8. Requirements and Prerequisites

Before running the application, install the following:

| Requirement | Purpose |
|---|---|
| Python 3.15.2 | Backend runtime used during prototype development |
| Node.js | Frontend development environment |
| npm | Frontend package management |
| MySQL Server 8.0 | Database server |
| MySQL Workbench | Database administration |
| FFmpeg | Audio conversion |
| Git | Version control |

The frontend package configuration requires Node.js `^22.18.0` or `>=24.12.0`.

FFmpeg must be installed separately and accessible through the system PATH.

yt-dlp may also use Node.js as its JavaScript runtime for supported YouTube extraction operations.

---

## 9. Installation and Configuration

### 9.1 Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/128-ytmp3.git
cd 128-ytmp3
```

Replace `YOUR_USERNAME` with the repository owner's GitHub username.

### 9.2 Install Frontend Dependencies

From the project root:

```bash
npm install
```

### 9.3 Set Up the Python Virtual Environment

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

For PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```bash
python -m pip install -r requirements.txt
```

### 9.4 Configure MySQL

1. Start MySQL Server.
2. Open MySQL Workbench.
3. Create the `ytmp3_beta` database.
4. Execute the SQL statements in `database/schema.sql`.

### 9.5 Configure Environment Variables

Create a local `.env` file inside the `backend/` directory.

Copy the contents of `.env.example`:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=ytmp3_beta
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD

MAX_VIDEO_SECONDS=1800
JS_RUNTIME=node
```

Replace `YOUR_MYSQL_PASSWORD` with your actual MySQL password.

If the local MySQL root account has no password, leave the value empty:

```env
DB_PASSWORD=
```

**Important:** Never commit your actual `.env` file. It contains database credentials.

---

## 10. Running the Application

The frontend and backend must run simultaneously in separate terminals.

### Terminal 1: Start the Backend

Navigate to the backend directory:

```cmd
cd backend
```

Activate the virtual environment:

```cmd
.venv\Scripts\activate.bat
```

Start the FastAPI development server:

```cmd
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be accessible at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

### Terminal 2: Start the Frontend

Navigate to the project root:

```cmd
cd 128-ytmp3
```

Start the Vite development server:

```bash
npm run dev
```

Vite will display the local frontend address, typically:

```text
http://localhost:5173
```

Open that address in your browser.

### Stopping the Servers

Press `CTRL + C` in the corresponding terminal to stop either server.

---

## 11. Using the Application

### 11.1 Create a Playlist

1. Open the application in your browser.
2. Enter a playlist name.
3. Paste YouTube video links into the link textbox.
4. Separate each link using a new line.
5. Make sure the number of non-empty links does not exceed ten.
6. Click **Import**.

The application validates the links and retrieves their metadata before saving the playlist.

### 11.2 View Playlist History

Successfully created playlists appear in the playlist history panel.

Each entry displays:

- Playlist name
- Number of tracks
- Track titles
- Track positions
- Canonical YouTube URLs

### 11.3 Export a Playlist

1. Select a saved playlist from the export dropdown.
2. Click **Export**.
3. Wait while the backend downloads and converts the tracks.
4. Observe the export status indicator.
5. Once processing finishes, the browser downloads the ZIP archive.

Extract the ZIP archive to access the numbered MP3 files.

---

## 12. API Endpoints

The FastAPI backend currently provides the following endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks whether the backend is running |
| GET | `/playlists` | Retrieves saved playlists and their tracks |
| POST | `/playlists` | Creates a new playlist from submitted links |
| POST | `/playlists/{playlist_id}/export` | Exports a selected playlist as a ZIP archive |

### 12.1 Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### 12.2 Retrieve Playlists

```http
GET /playlists
```

Returns saved playlists, their tracks, and the maximum number of links allowed per import.

### 12.3 Create a Playlist

```http
POST /playlists
Content-Type: application/json
```

Example request:

```json
{
  "name": "Family Favorites",
  "urls": [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  ]
}
```

A successful request returns the new playlist ID, track count, imported tracks, and any skipped duplicates.

### 12.4 Export a Playlist

```http
POST /playlists/1/export
```

The endpoint receives a playlist ID and returns a ZIP archive containing the converted MP3 files.

Interactive API documentation is available through:

```text
http://127.0.0.1:8000/docs
```

---

## 13. Testing

The backend includes automated tests for YouTube URL validation.

Run the tests from the `backend/` directory with the virtual environment activated:

```bash
python -m pytest tests/test_youtube.py -v
```

The validation tests cover:

- Standard YouTube video URLs.
- Shortened YouTube URLs.
- Shorts, embed, and live URLs.
- YouTube Music URLs.
- URLs with additional query parameters.
- Invalid and unsupported URLs.
- Non-YouTube domains.
- Lookalike domains.
- Malformed video IDs.
- Canonical URL generation.

The prototype's URL validation test suite passed all 16 test cases during development.

Metadata extraction and ZIP export were also manually verified using accessible test videos.

---

## 14. Current Limitations

This project is intentionally limited to a local proof of concept.

The following limitations are present in the current implementation:

### Application and Users

- No user registration or authentication.
- No individual user ownership of playlists.
- No playlist editing or deletion interface.
- No playlist sharing functionality.

### Import and Metadata

- A maximum of ten non-empty links per import.
- Metadata retrieval is performed sequentially.
- A failed video verification causes the entire import to fail.
- The configured maximum video duration is 30 minutes.
- Duplicate video IDs within one import are skipped.
- Existing song records are reused across different playlists.

### Export

- Export processing is synchronous.
- The frontend displays an indeterminate progress indicator rather than an exact percentage.
- There is no export cancellation or retry interface.
- Temporary files are cleaned up after the ZIP response is completed.
- Export depends on yt-dlp, FFmpeg, network connectivity, and video accessibility.

### Infrastructure and Security

- The backend is configured for local access.
- MySQL credentials are supplied through environment variables.
- The prototype does not implement production authentication or authorization.
- There is no background job queue or distributed processing infrastructure.
- There is no production deployment configuration.

These limitations are acceptable for the current demonstration scope and should be considered when developing the future system.

---

## 15. Future Development

The current implementation is intended to serve as a blueprint for a more complete family playlist management system.

Potential improvements include:

### 15.1 User Management

- User registration and authentication.
- Individual playlist ownership.
- Access control and authorization.
- User-specific playlist history.

### 15.2 Playlist Management

- Edit playlist details.
- Add or remove tracks.
- Reorder tracks.
- Delete playlists.
- Share playlists with other users.

### 15.3 Export Improvements

- Background export processing.
- Real-time progress tracking.
- Export cancellation and retry.
- Export history.
- Additional authorized output formats.

### 15.4 Security and Reliability

- Dedicated database accounts with restricted privileges.
- API authentication and authorization.
- Request rate limiting.
- Improved logging and error monitoring.
- Automated database backups.
- Better temporary file management.

### 15.5 Deployment and Scalability

- Production deployment configuration.
- Remote database hosting.
- Background job processing.
- Improved resource management.
- Automated testing and continuous integration.

These improvements are considerations for future development and are not part of the current proof of concept.

---

## 16. Legal and Usage Considerations

This application is a technical proof of concept for playlist organization and authorized audio export.

Users are responsible for ensuring that they have the necessary rights or authorization to download and convert any media processed through the application.

The application does not intend to bypass YouTube's access controls, restrictions, or content protection mechanisms.

Users and future developers should review applicable copyright laws, content licenses, and YouTube's terms of service before deploying or expanding the system.

---

## Acknowledgment

YT-MP3: Family Playlist Maker was developed as a proof of concept to demonstrate the integration of modern frontend technologies, a Python REST API, relational database storage, and audio processing tools.

The project is intended to provide a functional starting point and architectural reference for the development of a future family playlist management system.
