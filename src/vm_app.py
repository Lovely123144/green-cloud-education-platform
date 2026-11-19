"""Design A - the same logic behind a tiny WSGI app (run with gunicorn on EC2)."""
import json
import core


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    try:
        n = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        n = 0
    body = json.loads(environ["wsgi.input"].read(n) or b"{}") if n else {}
    if path.endswith("/login"):
        out = core.login(body.get("user", "u"), body.get("password", "p"))
    elif path.endswith("/courses"):
        out = json.loads(core.list_courses(int(body.get("page", 0))))
    elif path.endswith("/quiz"):
        out = core.grade_quiz(body.get("answers", []), body.get("essay", ""))
    elif path.endswith("/health"):
        out = {"status": "ok"}
    else:
        start_response("404 Not Found", [("Content-Type", "application/json")])
        return [b'{"error":"not found"}']
    start_response("200 OK", [("Content-Type", "application/json")])
    return [json.dumps(out).encode()]
