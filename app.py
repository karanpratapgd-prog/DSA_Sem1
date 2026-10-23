"""
Localhost web app for the FIFO tie-breaking priority scheduler.

Run:   python app.py            (opens http://127.0.0.1:8000 in your browser)
       python app.py --port 9000 --no-browser

Only the Python standard library is used. The server listens on 127.0.0.1
only, so it is reachable from your own computer and nowhere else.

API (JSON)
    GET  /api/state
    POST /api/insert   {"name": "Backup", "priority": 3}
    POST /api/extract  {}
    POST /api/reset    {}
    POST /api/fifo     {"use_fifo": true}
    POST /api/load     {"kind": "demo" | "ties"}
"""

import argparse
import copy
import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scheduler import FIFOPriorityScheduler

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
}

MAX_TASKS = 200
MAX_NAME_LEN = 40
MIN_PRIORITY, MAX_PRIORITY = 1, 5
MAX_BODY = 4096

DEMO_TASKS = [
    ("Backup Files", 3), ("Antivirus Scan", 2), ("Disk Cleanup", 4),
    ("Email Sync", 2), ("Software Update", 3), ("Print Document", 2),
]
TIE_TASKS = [(f"Task {c}", 2) for c in "ABCDEFG"]


class InputError(ValueError):
    """Raised for invalid user input; the message is safe to show to the user."""


class SchedulerService:
    """Holds the scheduler state for the web page. All methods are thread-safe."""

    def __init__(self):
        self._lock = threading.Lock()
        self._use_fifo = True
        self._sched = FIFOPriorityScheduler(use_fifo=True)
        self._ran = []          # tasks already executed, in order
        self._message = "Add a task to begin."

    # ---- validation ---------------------------------------------------- #
    @staticmethod
    def _clean_name(name):
        if not isinstance(name, str):
            raise InputError("Task name must be text.")
        name = " ".join(name.split())
        if not name:
            raise InputError("Please enter a task name.")
        if len(name) > MAX_NAME_LEN:
            raise InputError("Task name must be at most %d characters." % MAX_NAME_LEN)
        return name

    @staticmethod
    def _clean_priority(priority):
        if isinstance(priority, bool):
            raise InputError("Priority must be a whole number.")
        if isinstance(priority, str) and priority.strip().lstrip("+").isdigit():
            priority = int(priority.strip())
        if not isinstance(priority, int):
            raise InputError("Priority must be a whole number.")
        if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
            raise InputError("Priority must be between %d (highest) and %d (lowest)."
                             % (MIN_PRIORITY, MAX_PRIORITY))
        return priority

    # ---- actions ------------------------------------------------------- #
    def insert(self, name, priority):
        name = self._clean_name(name)
        priority = self._clean_priority(priority)
        with self._lock:
            if len(self._sched) >= MAX_TASKS:
                raise InputError("The queue is full (%d tasks)." % MAX_TASKS)
            t = self._sched.insert(name, priority)
            self._message = "Added %s (priority %d, arrival #%d)." % (t.name, t.priority, t.arrival_seq)
            return self._state_unlocked()

    def extract(self):
        with self._lock:
            t = self._sched.extract_next()
            if t is None:
                raise InputError("The queue is empty. Add a task first.")
            self._ran.append(t)
            self._message = "Ran %s (priority %d, arrival #%d)." % (t.name, t.priority, t.arrival_seq)
            return self._state_unlocked()

    def reset(self):
        with self._lock:
            self._reset_unlocked()
            self._message = "Queue cleared."
            return self._state_unlocked()

    def set_fifo(self, use_fifo):
        if not isinstance(use_fifo, bool):
            raise InputError("use_fifo must be true or false.")
        with self._lock:
            self._use_fifo = use_fifo
            self._sched.set_fifo(use_fifo)
            self._message = ("FIFO tie-break ON: equal priorities run in arrival order."
                             if use_fifo else
                             "FIFO tie-break OFF: equal priorities may run in any order.")
            return self._state_unlocked()

    def load(self, kind):
        if kind not in ("demo", "ties"):
            raise InputError("Unknown sample data set.")
        with self._lock:
            self._reset_unlocked()
            for name, prio in (DEMO_TASKS if kind == "demo" else TIE_TASKS):
                self._sched.insert(name, prio)
            self._message = ("Loaded the 6-task demo." if kind == "demo"
                             else "Loaded 7 tasks that all have priority 2.")
            return self._state_unlocked()

    def state(self):
        with self._lock:
            return self._state_unlocked()

    # ---- internals ----------------------------------------------------- #
    def _reset_unlocked(self):
        self._sched = FIFOPriorityScheduler(use_fifo=self._use_fifo)
        self._ran = []

    def _state_unlocked(self):
        # The true selection order: drain a copy so the real queue is untouched.
        clone = copy.deepcopy(self._sched)
        order = []
        while not clone.is_empty():
            order.append(clone.extract_next())
        row = lambda t: {"name": t.name, "priority": t.priority, "arrival": t.arrival_seq}
        return {
            "use_fifo": self._use_fifo,
            "queue": [row(t) for t in order],
            "heap": [row(t) for t in self._sched.heap_array()],
            "ran": [row(t) for t in self._ran],
            "message": self._message,
            "limits": {"min_priority": MIN_PRIORITY, "max_priority": MAX_PRIORITY,
                       "max_name": MAX_NAME_LEN},
        }


SERVICE = SchedulerService()


class Handler(BaseHTTPRequestHandler):
    server_version = "FifoScheduler/1.0"

    # -- helpers --
    def _host_ok(self):
        # Defends against DNS-rebinding: only accept requests addressed to localhost.
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        return host in ("127.0.0.1", "localhost", "::1")

    def _send(self, status, body, ctype):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, payload):
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json")

    def log_message(self, fmt, *args):   # quieter console
        print("  %s %s" % (self.command, self.path))

    # -- routes --
    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"error": "Forbidden host."})
        path = self.path.split("?", 1)[0]
        if path == "/api/state":
            return self._json(200, SERVICE.state())
        if path in STATIC_FILES:
            fname, ctype = STATIC_FILES[path]
            try:
                with open(os.path.join(STATIC_DIR, fname), "rb") as f:
                    return self._send(200, f.read(), ctype)
            except OSError:
                return self._json(500, {"error": "Missing static file: " + fname})
        self._json(404, {"error": "Not found."})

    def do_POST(self):
        if not self._host_ok():
            return self._json(403, {"error": "Forbidden host."})
        path = self.path.split("?", 1)[0]
        # Requiring a JSON content type blocks cross-site form posts.
        if (self.headers.get("Content-Type") or "").split(";")[0].strip() != "application/json":
            return self._json(415, {"error": "Content-Type must be application/json."})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._json(400, {"error": "Bad Content-Length."})
        if length > MAX_BODY:
            return self._json(413, {"error": "Request too large."})
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {"error": "Body must be a JSON object."})

        try:
            if path == "/api/insert":
                return self._json(200, SERVICE.insert(data.get("name"), data.get("priority")))
            if path == "/api/extract":
                return self._json(200, SERVICE.extract())
            if path == "/api/reset":
                return self._json(200, SERVICE.reset())
            if path == "/api/fifo":
                return self._json(200, SERVICE.set_fifo(data.get("use_fifo")))
            if path == "/api/load":
                return self._json(200, SERVICE.load(data.get("kind")))
        except InputError as e:
            return self._json(400, {"error": str(e)})
        self._json(404, {"error": "Not found."})


def make_server(port, tries=10):
    """Bind 127.0.0.1 on `port`, or the next free port if it is busy."""
    last_error = None
    for p in range(port, port + tries):
        try:
            return ThreadingHTTPServer(("127.0.0.1", p), Handler)
        except OSError as e:
            last_error = e
    raise SystemExit("Could not open a port in %d-%d: %s" % (port, port + tries - 1, last_error))


def main():
    parser = argparse.ArgumentParser(description="FIFO priority scheduler web app")
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default 8000)")
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    args = parser.parse_args()

    server = make_server(args.port)
    url = "http://127.0.0.1:%d" % server.server_address[1]
    print("FIFO Priority Scheduler running at", url)
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
