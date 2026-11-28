"""
Serves the built frontend (the `dist` folder from `npm run build`) from the
same address as the API. Used by the installed app; off in development.

Only three kinds of answer are possible, so no request can reach a file
outside `dist`:
- /assets/...           the built JavaScript and CSS (Starlette's StaticFiles
                        refuses paths that leave the folder);
- a top-level file      only names that were in `dist` when the server started
                        (icons), matched exactly, never joined from the URL;
- anything else         index.html, and the Vue router shows the right page.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, dist_dir: str | Path) -> Path:
    """Serve the app from `dist_dir`. Call it after every API route is added."""
    dist = Path(dist_dir).resolve()
    index = dist / "index.html"
    if not index.is_file():
        raise RuntimeError(
            f"FRONTEND_DIST_DIR is set, but {index} doesn't exist. Run `npm run build`."
        )

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    top_level_files = {
        path.name: path for path in dist.iterdir() if path.is_file() and path.name != "index.html"
    }

    # index.html changes with every build, so the browser must always ask for
    # it again; the files it points to have the build's hash in their names.
    no_cache = {"Cache-Control": "no-cache"}

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        file = top_level_files.get(path)
        if file is not None:
            return FileResponse(file)
        return FileResponse(index, headers=no_cache)

    return dist
