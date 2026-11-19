"""Run all experiments and write CSV/JSON results to results/.

Measured input : CPU time of each endpoint (results/measured_workload.json).
Modelled input : AWS list prices, CCF power coefficients, synthetic hourly grid profiles,
                 queueing / container-reuse behaviour (discrete-event simulation).
"""
import heapq, json, math, os, sys, time
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import carbon_model as cm, grid, scheduler as sch

RES = os.path.join(ROOT, "results"); os.makedirs(RES, exist_ok=True)
meas = json.load(open(os.path.join(RES, "measured_workload.json")))

# ------------------------------------------------------------------ assumptions
OVERHEAD_CPU_MS = 3.0                      # runtime / JSON / proxy handling per request (assumed)
TYPES = ["login", "list_courses", "submit_quiz"]
CPU_S = np.array([(meas[t]["mean_ms"] + OVERHEAD_CPU_MS) / 1000 for t in TYPES])   # at 1 vCPU
IO_S = np.array([12, 8, 15]) / 1000        # DB read/write wait (assumed)
MIX_NORMAL = np.array([0.20, 0.55, 0.25])
MIX_EXAM = np.array([0.15, 0.25, 0.60])
HOME = "ap-northeast-1"; LOCAL_UTC = 8     # students in UTC+8, region Tokyo (UTC+9)
COLD_S, KEEPALIVE_S = 0.30, 900            # cold start & container keep-alive (assumed)
HOUR_W = np.array([.3,.2,.15,.1,.1,.2,.5,1.5,3.5,5.5,6,5,3.5,3.5,5.5,6,5,3.5,3,4.5,6,6,4,1.5])
SEED = 42


def day_counts(n_req, exam=False, rng=None):
    w = HOUR_W.copy()
    if exam:
        w[14] *= 5; w[15] *= 5
    w = w / w.sum()
    return rng.poisson(n_req * w), w


def make_arrivals(n_req, exam, rng):
    counts, _ = day_counts(n_req, exam, rng)
    times = np.concatenate([h * 3600 + np.sort(rng.random(c) * 3600) for h, c in enumerate(counts)])
    mix = MIX_EXAM if exam else MIX_NORMAL
    types = rng.choice(3, size=times.size, p=mix)
    return times, types


def intensity_utc_for_local_day(region, n_days=1, seed=0):
    """Intensity indexed by LOCAL (UTC+8) hour 0..23 of the simulated day."""
    s = grid.actual_series(region, 3, seed=seed, noise_sd=0.0)      # 72 h, deterministic
    utc_idx = (np.arange(24) - LOCAL_UTC) % 24 + 24                 # middle day
    return s[utc_idx]


# ------------------------------------------------------------------ simulators
def sim_lambda(times, types, mem_mb, arch="arm", cold_s=COLD_S, keep=KEEPALIVE_S, idle_factor=1.0):
    share = min(mem_mb / cm.MB_PER_VCPU, 1.0)
    warm = CPU_S[types] / share + IO_S[types]
    heap, lat, cold_flags, dur_billed = [], np.empty(times.size), np.zeros(times.size, bool), np.empty(times.size)
    peak = 0
    for i, t in enumerate(times):
        while heap and heap[0] + keep < t:
            heapq.heappop(heap)
        if heap and heap[0] <= t:
            heapq.heappop(heap); d = warm[i]
        else:
            d = warm[i] + cold_s; cold_flags[i] = True
        heapq.heappush(heap, t + d)
        lat[i] = d; dur_billed[i] = d
        if len(heap) > peak: peak = len(heap)
    cost = sum(cm.lambda_cost_usd(d, mem_mb, arch) for d in dur_billed)
    e_req = np.array([cm.lambda_energy_wh(d, mem_mb, idle_factor=idle_factor) for d in dur_billed])
    hour = (times // 3600).astype(int)
    e_hour = np.bincount(hour, weights=e_req, minlength=24)
    return dict(lat=lat, cost=cost, e_hour=e_hour, cold=cold_flags.mean(), peak_containers=peak)


def sim_vm(times, types, n_inst):
    c = n_inst * cm.EC2_VCPU
    free = [0.0] * c; heapq.heapify(free)
    lat = np.empty(times.size); busy_h = np.zeros(24)
    cpu = CPU_S[types]
    for i, t in enumerate(times):
        f = heapq.heappop(free); start = max(t, f)
        heapq.heappush(free, start + cpu[i])
        lat[i] = (start - t) + cpu[i] + IO_S[types[i]]
    hour = (times // 3600).astype(int)
    busy_h = np.bincount(hour, weights=cpu, minlength=24)
    util_h = busy_h / (3600 * c)
    e_hour = np.array([cm.ec2_energy_wh(1, min(u, 1.0), n_inst) for u in util_h])
    cost = cm.ec2_cost_usd(24, n_inst, lcu=1.0)
    return dict(lat=lat, cost=cost, e_hour=e_hour, util_h=util_h)


def size_vm(n_req, exam, target=0.6):
    _, w = day_counts(n_req, exam, np.random.default_rng(0))
    mix = MIX_EXAM if exam else MIX_NORMAL
    cpu_mean = float((mix * CPU_S).sum())
    peak_vcpu = n_req * w.max() / 3600 * cpu_mean
    return max(2, math.ceil(peak_vcpu / target / cm.EC2_VCPU))


def pct(a, q): return float(np.percentile(a, q) * 1000)


# ------------------------------------------------------------------ EXP 1: memory sweep
def exp1():
    rows = []
    prof = {"API mix (I/O-dominated)": (float((MIX_NORMAL * CPU_S).sum()), float((MIX_NORMAL * IO_S).sum())),
            "Batch grading (CPU-dominated, 1.5 s CPU)": (1.5, 0.05)}
    inten = float(intensity_utc_for_local_day(HOME).mean())
    for name, (cpu, io) in prof.items():
        for arch in ["x86", "arm"]:
            for mem in [128, 256, 512, 1024, 1769, 2560, 3008]:
                d = cm.lambda_duration_s(cpu, io, mem)
                cost = cm.lambda_cost_usd(d, mem, arch, api_gw=False) * 1e6
                e = cm.lambda_energy_wh(d, mem) * 1000
                rows.append(dict(workload=name, arch=arch, mem_mb=mem, duration_ms=d * 1000,
                                 cost_usd_per_M=cost, energy_Wh_per_1000=e,
                                 gCO2_per_1000=cm.carbon_g(e, inten)))
    df = pd.DataFrame(rows); df.to_csv(f"{RES}/exp1_memory_sweep.csv", index=False); return df


# ------------------------------------------------------------------ EXP 2: Design A vs B
SCENARIOS = {
    "Campus - normal day": (300_000, False),
    "Campus - exam day": (900_000, True),
    "Large - exam day": (5_400_000, True),
}
B_MEM = 256


def exp2():
    rows, hourly = [], {}
    inten = intensity_utc_for_local_day(HOME)
    for name, (n, exam) in SCENARIOS.items():
        rng = np.random.default_rng(SEED)
        t, ty = make_arrivals(n, exam, rng)
        nA = size_vm(n, exam)
        A = sim_vm(t, ty, nA); B = sim_lambda(t, ty, B_MEM, "arm"); F = sim_lambda(t, ty, 1769, "arm")
        for tag, R, extra in [("A: EC2+ALB", A, dict(instances=nA)),
                              ("B: Lambda arm64 256MB", B, dict(cold_pct=100 * B["cold"])),
                              ("B-fast: Lambda arm64 1769MB", F, dict(cold_pct=100 * F["cold"]))]:
            cost = R["cost"]
            e = R["e_hour"].sum(); g = float((R["e_hour"] / 1000 * inten).sum())
            rows.append(dict(scenario=name, design=tag, requests=len(t), cost_usd=cost,
                             energy_Wh=e, gCO2=g, gCO2_per_1000req=g / len(t) * 1000,
                             usd_per_1M=cost / len(t) * 1e6,
                             p50_ms=pct(R["lat"], 50), p95_ms=pct(R["lat"], 95), p99_ms=pct(R["lat"], 99),
                             mean_util_pct=(100 * R["util_h"].mean() if "util_h" in R else np.nan),
                             peak_util_pct=(100 * R["util_h"].max() if "util_h" in R else np.nan),
                             **extra))
        hourly[name] = dict(req=np.bincount((t // 3600).astype(int), minlength=24).tolist(),
                            eA=A["e_hour"].tolist(), eB=B["e_hour"].tolist(), utilA=A["util_h"].tolist(),
                            gA=(A["e_hour"] / 1000 * inten).tolist(), gB=(B["e_hour"] / 1000 * inten).tolist())
    df = pd.DataFrame(rows); df.to_csv(f"{RES}/exp2_design_comparison.csv", index=False)
    json.dump(dict(hourly=hourly, intensity=inten.tolist()), open(f"{RES}/exp2_hourly.json", "w"))
    return df


# ------------------------------------------------------------------ EXP 3: region
def exp3():
    df2 = pd.read_csv(f"{RES}/exp2_design_comparison.csv")
    out = []
    h = json.load(open(f"{RES}/exp2_hourly.json"))["hourly"]["Campus - normal day"]
    eB = np.array(h["eB"]); eA = np.array(h["eA"])
    base = {}
    for r in grid.REGIONS:
        inten = intensity_utc_for_local_day(r)
        gB = float((eB / 1000 * inten).sum()); gA = float((eA / 1000 * inten).sum())
        base[r] = (gA, gB, float(inten.mean()))
    for r, (gA, gB, im) in base.items():
        out.append(dict(region=r, mean_intensity=im, gCO2_A=gA, gCO2_B=gB,
                        B_vs_home_pct=100 * (gB / base[HOME][1] - 1)))
    df = pd.DataFrame(out); df.to_csv(f"{RES}/exp3_regions.csv", index=False); return df


# ------------------------------------------------------------------ EXP 4: scheduler
JOBS = {  # name: (vcpus, duration_h, ready_local_hour, deadline_h, data_GB moved if run abroad)
    "Nightly grading & reports": (8, 2, 23, 9, 1),
    "Lecture-video transcoding": (8, 8, 18, 24, 20),
}


def run_sched(strategy, job, n_days=60, err=0.06, amp=1.0, deadline_override=None, seed=3):
    vcpus, dur, ready_local, dl, data_gb = JOBS[job]
    dl = deadline_override if deadline_override is not None else dl
    horizon = n_days * 24 + 96
    act = {r: grid.actual_series(r, horizon // 24 + 1, seed=seed, amp=amp) for r in grid.REGIONS}
    fc = {r: grid.forecast_from(a, err, seed=seed + 11) for r, a in act.items()}
    e_wh = cm.batch_energy_wh(vcpus, dur)
    move_pen = 0.0
    res = []
    for d in range(1, n_days + 1):
        now = d * 24 + (ready_local - LOCAL_UTC) % 24
        if strategy == "immediate":
            r, s = HOME, now
        elif strategy == "temporal":
            r, s = HOME, sch.best_start(fc[HOME], now, dur, dl)
        elif strategy == "spatial":
            r, s = sch.best_region_start(fc, now, dur, dur, home=HOME)   # no waiting allowed
        elif strategy == "spatiotemporal":
            r, s = sch.best_region_start(fc, now, dur, dl, home=HOME)
        g = cm.carbon_g(e_wh, float(np.mean(act[r][s:s + dur])))
        # network energy 0.001 kWh/GB (CCF), charged at the home-grid intensity (conservative)
        gb = data_gb * 0.001 * float(act[HOME][now]) if r != HOME else 0.0
        res.append((g + gb, s - now, r))
    g = np.array([x[0] for x in res])
    return g.mean(), g.std(), np.mean([x[1] for x in res]), pd.Series([x[2] for x in res]).value_counts().to_dict()


def exp4():
    rows = []
    for job in JOBS:
        base = run_sched("immediate", job)[0]
        for st in ["immediate", "temporal", "spatial", "spatiotemporal"]:
            m, sd, delay, regs = run_sched(st, job)
            rows.append(dict(job=job, strategy=st, mean_gCO2=m, sd_gCO2=sd,
                             saving_pct=100 * (1 - m / base), mean_delay_h=delay, regions=json.dumps(regs)))
    df = pd.DataFrame(rows); df.to_csv(f"{RES}/exp4_scheduler.csv", index=False)
    # sweep: flexibility window, forecast error, grid variability
    sw = []
    for job in JOBS:
        base = run_sched("immediate", job)[0]
        for D in [0, 3, 6, 9, 12, 18, 24, 36]:
            dur = JOBS[job][1]
            Dm = max(D, dur)
            m = run_sched("temporal", job, deadline_override=Dm)[0]
            sw.append(dict(job=job, sweep="window_h", x=D, saving_pct=100 * (1 - m / base)))
        for e in [0, 0.03, 0.06, 0.10, 0.20, 0.40]:
            m = run_sched("temporal", job, err=e, deadline_override=24)[0]
            sw.append(dict(job=job, sweep="forecast_err", x=e, saving_pct=100 * (1 - m / base)))
        for a in [0.0, 0.5, 1.0, 1.5, 2.0]:
            b0 = run_sched("immediate", job, amp=a)[0]
            m = run_sched("temporal", job, amp=a, deadline_override=24)[0]
            sw.append(dict(job=job, sweep="grid_variability", x=a, saving_pct=100 * (1 - m / b0)))
    pd.DataFrame(sw).to_csv(f"{RES}/exp4_sweeps.csv", index=False)
    return df


# ------------------------------------------------------------------ EXP 5: break-even
def exp5():
    inten = intensity_utc_for_local_day(HOME)
    w = HOUR_W / HOUR_W.sum()
    cpu_mean = float((MIX_NORMAL * CPU_S).sum()); io_mean = float((MIX_NORMAL * IO_S).sum())
    d_warm = cm.lambda_duration_s(cpu_mean, io_mean, B_MEM)
    d_avg = d_warm + 0.005 * COLD_S                       # 0.5 % cold starts (assumed)
    rows = []
    for V in np.logspace(4, 9, 41):
        nA = max(2, math.ceil(V * w.max() / 3600 * cpu_mean / 0.6 / cm.EC2_VCPU))
        util_h = np.minimum(V * w * cpu_mean / (3600 * nA * cm.EC2_VCPU), 1.0)
        eA = np.array([cm.ec2_energy_wh(1, u, nA) for u in util_h])
        gA = float((eA / 1000 * inten).sum()); cA = cm.ec2_cost_usd(24, nA)
        cB = V * cm.lambda_cost_usd(d_avg, B_MEM, "arm")
        row = dict(req_per_day=V, instances=nA, cost_A=cA, cost_B=cB, gCO2_A=gA)
        for f in [1.0, 1.5, 2.0]:
            eB = V * cm.lambda_energy_wh(d_avg, B_MEM, idle_factor=f)
            row[f"gCO2_B_idle{f}"] = float(eB / 1000 * (w * inten).sum())
        rows.append(row)
    df = pd.DataFrame(rows); df.to_csv(f"{RES}/exp5_breakeven.csv", index=False)
    summ = {}
    for key in ["cost", "gCO2_idle1.0", "gCO2_idle1.5", "gCO2_idle2.0"]:
        if key == "cost": a, b = df.cost_A, df.cost_B
        else: a, b = df.gCO2_A, df[f"gCO2_B_{key.split('_')[1]}"]
        idx = np.where(a.values < b.values)[0]
        summ[key] = float(df.req_per_day.values[idx[0]]) if idx.size else None
    json.dump(summ, open(f"{RES}/exp5_crossovers.json", "w"), indent=2)
    return df, summ


# ------------------------------------------------------------------ EXP 6: sensitivity analysis
def analytic_day(V=300_000, mix=MIX_NORMAL, u_lambda=0.5, idle=1.0, io_scale=1.0, cpu_scale=1.0, cold_frac=2e-5,
                 wmin=None, wmax=None, wmem=None, apigw=None, mem=B_MEM):
    """Closed-form daily totals for A and B (used for one-at-a-time sensitivity)."""
    saved = (cm.W_MIN, cm.W_MAX, cm.W_MEM_PER_GB, cm.API_GW_REQ_USD)
    try:
        if wmin is not None: cm.W_MIN = wmin
        if wmax is not None: cm.W_MAX = wmax
        if wmem is not None: cm.W_MEM_PER_GB = wmem
        if apigw is not None: cm.API_GW_REQ_USD = apigw / 1e6
        inten = intensity_utc_for_local_day(HOME); w = HOUR_W / HOUR_W.sum()
        cpu = float((mix * CPU_S).sum()) * cpu_scale; io = float((mix * IO_S).sum()) * io_scale
        nA = max(2, math.ceil(V * w.max() / 3600 * cpu / 0.6 / cm.EC2_VCPU))
        util_h = np.minimum(V * w * cpu / (3600 * nA * cm.EC2_VCPU), 1.0)
        eA = np.array([cm.ec2_energy_wh(1, u, nA) for u in util_h])
        gA = float((eA / 1000 * inten).sum()); cA = cm.ec2_cost_usd(24, nA)
        d = cm.lambda_duration_s(cpu, io, mem) + cold_frac * COLD_S
        cB = V * cm.lambda_cost_usd(d, mem, "arm")
        gB = float(V * cm.lambda_energy_wh(d, mem, util=u_lambda, idle_factor=idle) / 1000 * (w * inten).sum())
        return cA, gA, cB, gB
    finally:
        cm.W_MIN, cm.W_MAX, cm.W_MEM_PER_GB, cm.API_GW_REQ_USD = saved


def exp6():
    base = analytic_day(); rows = [dict(parameter="baseline", low="-", high="-", cost_ratio_low=base[2] / base[0], cost_ratio_high=base[2] / base[0],
                                        co2_ratio_low=base[3] / base[1], co2_ratio_high=base[3] / base[1])]
    cases = [("Lambda CPU utilisation u (0.5)", "0.25", "1.0", dict(u_lambda=0.25), dict(u_lambda=1.0)),
             ("Provider idle overhead on Lambda (1.0)", "1.0", "3.0", dict(idle=1.0), dict(idle=3.0)),
             ("I/O wait per request (x1)", "x0.5", "x2", dict(io_scale=0.5), dict(io_scale=2.0)),
             ("CPU time per request (x1)", "x0.5", "x2", dict(cpu_scale=0.5), dict(cpu_scale=2.0)),
             ("Cold-start share of requests (0.002 %)", "0 %", "2 %", dict(cold_frac=0.0), dict(cold_frac=0.02)),
             ("Idle power per vCPU (0.74 W)", "0.37 W", "1.11 W", dict(wmin=0.37), dict(wmin=1.11)),
             ("Peak power per vCPU (3.5 W)", "1.75 W", "5.25 W", dict(wmax=1.75), dict(wmax=5.25)),
             ("Memory power (0.392 W/GB)", "0", "0.784", dict(wmem=0.0), dict(wmem=0.784)),
             ("Daily request volume (300k)", "30k", "3M", dict(V=30_000), dict(V=3_000_000)),
             ("API gateway price (USD 1.00/M)", "USD 0", "USD 2.00", dict(apigw=0.0), dict(apigw=2.0))]
    for name, lo, hi, kl, kh in cases:
        a = analytic_day(**kl); b = analytic_day(**kh)
        rows.append(dict(parameter=name, low=lo, high=hi, cost_ratio_low=a[2] / a[0], cost_ratio_high=b[2] / b[0],
                         co2_ratio_low=a[3] / a[1], co2_ratio_high=b[3] / b[1]))
    df = pd.DataFrame(rows); df.to_csv(f"{RES}/exp6_sensitivity.csv", index=False)
    json.dump(dict(cost_A=base[0], co2_A=base[1], cost_B=base[2], co2_B=base[3]), open(f"{RES}/exp6_baseline.json", "w"))
    return df


# ------------------------------------------------------------------ EXP 7: stronger baselines
PRICES = {"A: t3.medium on-demand": 0.0416, "A-RI: t3.medium 1-yr reserved": 0.029,
          "A-arm: t4g.medium on-demand": 0.0336, "A-arm-RI: t4g.medium 1-yr reserved": 0.0196}


def exp7():
    rows = []
    for name, (n, exam) in SCENARIOS.items():
        rng = np.random.default_rng(SEED); t, ty = make_arrivals(n, exam, rng); nA = size_vm(n, exam)
        A = sim_vm(t, ty, nA); B = sim_lambda(t, ty, B_MEM, "arm"); F = sim_lambda(t, ty, 1769, "arm")
        inten = intensity_utc_for_local_day(HOME); gA = float((A["e_hour"] / 1000 * inten).sum())
        for lab, price in PRICES.items():
            cost = nA * price * 24 + (cm.ALB_USD_HR + cm.ALB_LCU_USD_HR) * 24
            rows.append(dict(scenario=name, design=lab, cost_usd=cost, gCO2=gA, requests=len(t)))
        for lab, R in [("B: Lambda arm64 256MB", B), ("B-fast: Lambda arm64 1769MB", F)]:
            rows.append(dict(scenario=name, design=lab, cost_usd=R["cost"], gCO2=float((R["e_hour"] / 1000 * inten).sum()), requests=len(t)))
    df = pd.DataFrame(rows); df.to_csv(f"{RES}/exp7_baselines.csv", index=False); return df


# ------------------------------------------------------------------ EXP 8: flash crowd at exam start
def exp8():
    rng = np.random.default_rng(SEED + 5)
    t0, ty0 = make_arrivals(900_000, True, rng)
    nb = 20_000
    tb = 14 * 3600 + np.sort(rng.random(nb) * 10.0)            # 20,000 requests within 10 s at 14:00:00
    tyb = rng.choice([0, 2], size=nb)                          # half login, half quiz submission
    t = np.concatenate([t0, tb]); ty = np.concatenate([ty0, tyb]); o = np.argsort(t, kind="stable"); t, ty = t[o], ty[o]
    is_b = np.zeros(t.size, bool); is_b[np.searchsorted(t, 14 * 3600, "left"):np.searchsorted(t, 14 * 3600 + 10.0001, "right")] = True
    # burst mask: arrivals in the 10-s window that belong to the burst (some base traffic is in there too - negligible)
    rows, tails = [], {}
    def stats(name, lat, extra):
        w = lat[is_b]
        rows.append(dict(design=name, burst_requests=int(is_b.sum()),
                         slo_viol_burst_pct=100 * float((w > 0.1).mean()), slo_viol_day_pct=100 * float((lat > 0.1).mean()),
                         p50_ms=pct(w, 50), p99_ms=pct(w, 99), p999_ms=pct(w, 99.9), max_ms=float(w.max() * 1000), **extra))
        tails[name] = np.sort(w)[::max(1, w.size // 400)].tolist()
    for n_inst in [2, 7]:
        A = sim_vm(t, ty, n_inst); stats(f"A: {n_inst} x t3.medium", A["lat"], dict(cold_starts=0, daily_cost_usd=cm.ec2_cost_usd(24, n_inst)))
    for lab, mem, cold, keep in [("B: Lambda 256 MB, cold 0.3 s", 256, 0.3, 900), ("B: Lambda 256 MB, cold 1.0 s", 256, 1.0, 900),
                                 ("B: Lambda 256 MB, cold 0.3 s, keep-alive 1 min", 256, 0.3, 60), ("B-fast: Lambda 1769 MB, cold 0.3 s", 1769, 0.3, 900)]:
        R = sim_lambda(t, ty, mem, "arm", cold_s=cold, keep=keep)
        # count cold starts in burst
        warm = CPU_S[ty] / min(mem / cm.MB_PER_VCPU, 1.0) + IO_S[ty]
        coldmask = (R["lat"] - warm) > 1e-9
        stats(lab, R["lat"], dict(cold_starts=int(coldmask[is_b].sum()), daily_cost_usd=R["cost"]))
    df = pd.DataFrame(rows); df.to_csv(f"{RES}/exp8_flash_crowd.csv", index=False)
    json.dump(tails, open(f"{RES}/exp8_tails.json", "w"))
    return df


if __name__ == "__main__":
    t0 = time.time()
    print("Exp1 ..."); exp1()
    print("Exp2 ..."); d2 = exp2(); print(d2.round(3).to_string()); print(f"  [{time.time()-t0:.0f}s]")
    print("Exp3 ..."); print(exp3().round(2).to_string())
    print("Exp4 ..."); print(exp4().round(2).to_string())
    print("Exp5 ..."); _, s = exp5(); print(s)
    print("Exp6 ..."); print(exp6().round(4).to_string())
    print("Exp7 ..."); print(exp7().round(3).to_string())
    print("Exp8 ..."); print(exp8().round(2).to_string())
    print(f"done in {time.time()-t0:.0f}s")
