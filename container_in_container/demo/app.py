import os
import platform
import socket
import subprocess
import time
from collections import deque

import flask as flask_module
from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 8080))
START_TIME = time.time()
REQUEST_LOG = deque(maxlen=20)
RECENT_REQUESTS_RESPONSE_LIMIT = 10


def _get_podman_version():
    try:
        out = subprocess.check_output(["podman", "--version"], text=True).strip()
        return out.split()[-1]
    except Exception:
        return "unavailable"


def _get_os_name():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return f"{platform.system()} {platform.version()}".strip() or "unknown"


PODMAN_VERSION = _get_podman_version()
OS_NAME = _get_os_name()


@app.before_request
def _before():
    g.start = time.time()


@app.after_request
def _after(response):
    duration_ms = round((time.time() - g.start) * 1000)
    REQUEST_LOG.appendleft(
        {
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }
    )
    return response


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify(
        {
            "hostname": socket.gethostname(),
            "python_version": platform.python_version(),
            "flask_version": flask_module.__version__,
            "podman_version": PODMAN_VERSION,
            "os": OS_NAME,
            "port": PORT,
            "uptime_seconds": round(time.time() - START_TIME),
            "recent_requests": list(REQUEST_LOG)[:RECENT_REQUESTS_RESPONSE_LIMIT],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
