"""Measure the real CPU time of each endpoint (this is the only *measured* input
of the simulation; everything else is documented pricing / power coefficients)."""
import json, os, platform, random, statistics, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import core

random.seed(7)
LETTERS = "ABCD"
WORDS = ("cloud elastic virtual machine container serverless storage network "
         "scaling pooling service model hypervisor kubernetes").split()


def rand_sub():
    return {"answers": [random.choice(LETTERS) for _ in range(10)],
            "essay": " ".join(random.choice(WORDS) for _ in range(random.randint(25, 60)))}


def bench(fn, n, warm=50):
    for _ in range(warm):
        fn()
    xs = []
    for _ in range(n):
        t0 = time.process_time_ns()
        fn()
        xs.append((time.process_time_ns() - t0) / 1e6)   # ms of CPU
    xs.sort()
    return {"mean_ms": statistics.mean(xs), "p50_ms": xs[len(xs)//2],
            "p95_ms": xs[int(len(xs)*0.95)], "n": n}


subs = [rand_sub() for _ in range(2000)]
it = iter(range(10**9))
res = {
    "login": bench(lambda: core.login("student", "pass1234"), 1500),
    "list_courses": bench(lambda: core.list_courses(0), 5000),
    "submit_quiz": bench(lambda: (lambda s: core.grade_quiz(s["answers"], s["essay"]))(subs[next(it) % 2000]), 3000),
}
res["_machine"] = {"cpu": platform.processor() or "x86_64 Xeon @2.1GHz (1 vCPU sandbox)",
                   "python": platform.python_version(), "timer": "time.process_time"}
os.makedirs("results", exist_ok=True)
json.dump(res, open("results/measured_workload.json", "w"), indent=2)
for k, v in res.items():
    if not k.startswith("_"):
        print(f"{k:14s} mean={v['mean_ms']:.3f} ms  p95={v['p95_ms']:.3f} ms")
