"""
Playlist export (use case B8).

The modules match the participants in the export sequence diagram:
    service.py    PlaylistExportService  (runs the job, always cleans up)
    audio.py      AudioProcessor         (YouTube link -> MP3)
    packager.py   FilePackager           (MP3s -> verified ZIP)
    workspace.py  TemporaryFileManager   (temporary folders and expiry)
PlaylistService is SupabaseStore (ownership check, songs in saved order).
"""
