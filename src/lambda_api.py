"""Design B - AWS Lambda entry point (API Gateway / Function URL, proxy format)."""
import json
import core


def handler(event, context):
    path = event.get("rawPath") or event.get("path", "/")
    body = json.loads(event.get("body") or "{}")
    if path.endswith("/login"):
        out = core.login(body.get("user", "u"), body.get("password", "p"))
    elif path.endswith("/courses"):
        out = json.loads(core.list_courses(int(body.get("page", 0))))
    elif path.endswith("/quiz"):
        out = core.grade_quiz(body.get("answers", []), body.get("essay", ""))
    else:
        return {"statusCode": 404, "body": json.dumps({"error": "not found"})}
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(out)}
