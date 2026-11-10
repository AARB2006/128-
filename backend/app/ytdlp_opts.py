
from .config import JS_RUNTIME


def base_options():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 2,
        "extractor_retries": 1,

        # Use the installed Node.js runtime.
        "js_runtimes": {
            JS_RUNTIME: {}
        },
    }
