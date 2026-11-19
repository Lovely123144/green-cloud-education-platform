"""AWS deployment stub of the scheduler (not executed in the sandbox - needs AWS access).

Triggered by EventBridge when a batch job becomes ready. It reads a carbon-intensity
forecast (Electricity Maps style JSON), picks the best start hour with scheduler.best_start,
and creates a one-time EventBridge Scheduler entry that invokes the batch Lambda/Fargate task.
If the forecast API is unreachable it falls back to 'run now' so the deadline is never missed.
"""
import datetime as dt
import json
import os
import urllib.request

import numpy as np
from scheduler import best_start

API = os.environ.get("CARBON_API", "https://api.electricitymap.org/v3/carbon-intensity/forecast")
TOKEN = os.environ.get("CARBON_TOKEN", "")
ZONE = os.environ.get("ZONE", "JP-TK")
TARGET_ARN = os.environ.get("TARGET_ARN", "")
ROLE_ARN = os.environ.get("ROLE_ARN", "")


def _forecast():
    req = urllib.request.Request(f"{API}?zone={ZONE}", headers={"auth-token": TOKEN})
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.load(r)["forecast"]
    return [p["carbonIntensity"] for p in data]


def handler(event, context):
    duration_h = float(event.get("duration_h", 2))
    deadline_h = float(event.get("deadline_h", 9))
    try:
        start = best_start(np.array(_forecast(), dtype=float), 0, duration_h, deadline_h)
    except Exception:                       # API down -> run immediately
        start = 0
    when = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=start)
    if start > 0 and TARGET_ARN:
        import boto3                        # imported lazily: only available on AWS
        boto3.client("scheduler").create_schedule(
            Name=f"batch-{when:%Y%m%d%H}", ScheduleExpression=f"at({when:%Y-%m-%dT%H:%M:%S})",
            FlexibleTimeWindow={"Mode": "OFF"}, ActionAfterCompletion="DELETE",
            Target={"Arn": TARGET_ARN, "RoleArn": ROLE_ARN, "Input": json.dumps(event)})
    return {"start_in_hours": start, "start_utc": when.isoformat()}
