"""Load test for both designs:  locust -f loadtest/locustfile.py --host https://<your-endpoint>
Run once against Design A (ALB DNS name) and once against Design B (Function URL / API Gateway),
with identical user counts, then compare Locust's latency percentiles with CloudWatch metrics."""
import random
from locust import HttpUser, task, between

L = "ABCD"
ESSAY = "cloud computing provides elastic on-demand resources through virtualization and containers"


class Student(HttpUser):
    wait_time = between(1, 5)

    @task(2)
    def login(self):
        self.client.post("/login", json={"user": f"s{random.randint(1, 9999)}", "password": "pass1234"})

    @task(5)
    def courses(self):
        self.client.post("/courses", json={"page": random.randint(0, 2)})

    @task(3)
    def quiz(self):
        self.client.post("/quiz", json={"answers": [random.choice(L) for _ in range(10)], "essay": ESSAY})
