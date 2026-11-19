import json, os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.join(os.path.dirname(__file__), ".."); R = os.path.join(ROOT, "results"); F = os.path.join(ROOT, "figures")
os.makedirs(F, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "font.size": 9, "axes.grid": True, "grid.alpha": .25, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 100, "savefig.dpi": 220, "savefig.bbox": "tight"})
C = {"A": "#c0504d", "B": "#2e75b6", "F": "#7f9fcf", "G": "#4f9d5d", "K": "#555555"}


def box(ax, x, y, w, h, text, fc="#eef3fa", ec="#2e75b6", fs=7.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, p, q, text=None, style="-|>", ls="-", color="#333", dy=0.12):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=9, lw=1, color=color, ls=ls))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + dy, text, ha="center", fontsize=6.5, color=color)


# ---------------------------------------------------------------- Fig 1 architectures
def fig_arch():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.6))
    for ax in axes:
        ax.set_xlim(0, 6); ax.set_ylim(0, 6.2); ax.axis("off"); ax.grid(False)
    a = axes[0]; a.set_title("Design A: always-on VMs (traditional)", fontsize=9, fontweight="bold")
    box(a, 2, 5.3, 2, .6, "Students (browser)", "#f2f2f2", "#777")
    box(a, 2, 4.2, 2, .6, "CloudFront + S3\n(static front-end)", "#fff4e0", "#d98a1c")
    box(a, 2, 3.2, 2, .6, "Application Load\nBalancer", "#eef3fa", "#2e75b6")
    box(a, .3, 1.8, 2.4, .9, "EC2 t3.medium\n(AZ-a, always on)\n2 vCPU, 4 GiB, gunicorn", "#fdecea", "#c0504d")
    box(a, 3.3, 1.8, 2.4, .9, "EC2 t3.medium\n(AZ-b, always on)\n2 vCPU, 4 GiB, gunicorn", "#fdecea", "#c0504d")
    box(a, 1.4, .3, 3.2, .8, "RDS (Multi-AZ)\nCloudWatch, IAM, WAF", "#eaf4ea", "#4f9d5d")
    arrow(a, (3, 5.3), (3, 4.8)); arrow(a, (3, 4.2), (3, 3.8)); arrow(a, (2.6, 3.2), (1.5, 2.7)); arrow(a, (3.4, 3.2), (4.5, 2.7))
    arrow(a, (1.5, 1.8), (2.4, 1.1)); arrow(a, (4.5, 1.8), (3.6, 1.1))
    b = axes[1]; b.set_title("Design B: serverless + carbon-aware batch", fontsize=9, fontweight="bold")
    box(b, 2, 5.3, 2, .6, "Students (browser)", "#f2f2f2", "#777")
    box(b, 2, 4.2, 2, .6, "CloudFront + S3\n(static front-end)", "#fff4e0", "#d98a1c")
    box(b, 2, 3.2, 2, .6, "API Gateway /\nFunction URL", "#eef3fa", "#2e75b6")
    box(b, .8, 1.8, 4.4, .9, "AWS Lambda (arm64, 256 MB)\nlogin | courses | quiz   -   scales 0 to N\npay-per-request, no idle servers", "#e3edf9", "#2e75b6")
    box(b, 1.4, .3, 3.2, .8, "DynamoDB (on-demand)\nCloudWatch, IAM, WAF", "#eaf4ea", "#4f9d5d")
    arrow(b, (3, 5.3), (3, 4.8)); arrow(b, (3, 4.2), (3, 3.8)); arrow(b, (3, 3.2), (3, 2.7)); arrow(b, (3, 1.8), (3, 1.1))
    fig.tight_layout(); fig.savefig(f"{F}/fig_architecture.png"); plt.close(fig)


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(7.0, 2.7)); ax.set_xlim(0, 13.2); ax.set_ylim(0, 4.6); ax.axis("off"); ax.grid(False)
    box(ax, .1, 3.0, 2.0, .9, "EventBridge\n'job ready'\n(duration, deadline)", "#f2f2f2", "#777")
    box(ax, 2.8, 3.0, 2.4, .9, "Scheduler Lambda\nbest_start() /\nbest_region_start()", "#e3edf9", "#2e75b6", bold=True)
    box(ax, 2.8, 1.3, 2.4, .9, "Carbon-intensity API\n(Electricity Maps)\nforecast per region", "#fff4e0", "#d98a1c")
    box(ax, 5.9, 3.0, 2.4, .9, "EventBridge Scheduler\none-time schedule\nat chosen hour", "#f2f2f2", "#777")
    box(ax, 9.9, 3.6, 2.4, .9, "Batch workers\nhome region (Tokyo)\nFargate / EC2 Spot", "#fdecea", "#c0504d")
    box(ax, 9.9, 2.1, 2.4, .9, "Batch workers\ngreen region (Stockholm)\nanonymised data only", "#eaf4ea", "#4f9d5d")
    box(ax, 5.9, .25, 6.4, .7, "CloudWatch + S3 results  ->  cost / energy / CO$_2$e analysis (Python)", "#eef3fa", "#2e75b6")
    arrow(ax, (2.1, 3.45), (2.8, 3.45)); arrow(ax, (5.2, 3.45), (5.9, 3.45)); arrow(ax, (4.0, 2.2), (4.0, 3.0), "forecast", dy=.08)
    arrow(ax, (8.3, 3.7), (9.9, 4.05), "clean now", dy=.12); arrow(ax, (8.3, 3.2), (9.9, 2.55), "greener\nelsewhere", dy=-.55)
    arrow(ax, (11.1, 2.1), (11.1, .95))
    ax.add_patch(FancyArrowPatch((12.3, 4.05), (12.3, .6), arrowstyle="-|>", mutation_scale=9, lw=1, color="#333", connectionstyle="arc3,rad=-0.25"))
    fig.tight_layout(); fig.savefig(f"{F}/fig_pipeline.png"); plt.close(fig)


# ---------------------------------------------------------------- Fig 3 memory sweep
def fig_memory():
    d = pd.read_csv(f"{R}/exp1_memory_sweep.csv"); wl = d.workload.unique()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
    for ax, w in zip(axes, wl):
        for arch, col, mk in [("x86", C["A"], "s"), ("arm", C["B"], "o")]:
            s = d[(d.workload == w) & (d.arch == arch)]
            ax.plot(s.mem_mb, s.cost_usd_per_M, color=col, marker=mk, ms=4, label=f"cost, {arch}")
        ax.set_xscale("log", base=2); ax.set_xlabel("Memory (MB)"); ax.set_ylabel("Lambda compute cost (USD per 1M requests)")
        ax.set_title(w, fontsize=8)
        ax2 = ax.twinx(); s = d[(d.workload == w) & (d.arch == "arm")]
        ax2.plot(s.mem_mb, s.duration_ms, color=C["K"], ls="--", marker="^", ms=3.5, label="duration"); ax2.set_yscale("log")
        ax2.set_ylabel("Duration (ms, log)"); ax2.grid(False); ax2.spines["right"].set_visible(True)
        h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=6.5, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.30), frameon=False)
        ax.set_xticks(s.mem_mb); ax.set_xticklabels([str(m) for m in s.mem_mb], fontsize=6.5, rotation=45)
    fig.tight_layout(); fig.savefig(f"{F}/fig_memory.png"); plt.close(fig)


# ---------------------------------------------------------------- Fig 4 hourly
def fig_hourly():
    j = json.load(open(f"{R}/exp2_hourly.json")); h = j["hourly"]["Campus - normal day"]; I = np.array(j["intensity"])
    hrs = np.arange(24); fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
    ax = axes[0]; ax.bar(hrs, np.array(h["req"]) / 1000, color="#b7c9e2", label="requests (k/h)")
    ax.set_xlabel("Local hour (UTC+8)"); ax.set_ylabel("Requests per hour (thousand)"); ax2 = ax.twinx()
    ax2.plot(hrs, I, color=C["G"], marker="o", ms=3, label="grid intensity (Tokyo)"); ax2.set_ylabel("gCO$_2$e / kWh"); ax2.grid(False); ax2.spines["right"].set_visible(True)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=6.5, loc="upper left")
    ax = axes[1]; ax.plot(hrs, h["gA"], color=C["A"], marker="s", ms=3, label="Design A (2 x t3.medium)")
    ax.plot(hrs, np.array(h["gB"]) * 1, color=C["B"], marker="o", ms=3, label="Design B (Lambda 256 MB)")
    ax.set_yscale("log"); ax.set_xlabel("Local hour (UTC+8)"); ax.set_ylabel("gCO$_2$e per hour (log)"); ax.legend(fontsize=6.5)
    fig.tight_layout(); fig.savefig(f"{F}/fig_hourly.png"); plt.close(fig)


# ---------------------------------------------------------------- Fig 5 designs
def fig_designs():
    d = pd.read_csv(f"{R}/exp2_design_comparison.csv"); sc = list(d.scenario.unique())
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8)); w = .26; x = np.arange(len(sc))
    for k, (des, col) in enumerate([("A: EC2+ALB", C["A"]), ("B: Lambda arm64 256MB", C["B"]), ("B-fast: Lambda arm64 1769MB", C["F"])]):
        s = d[d.design == des].set_index("scenario").loc[sc]
        axes[0].bar(x + (k - 1) * w, s.cost_usd, w, color=col, label=des.split(":")[0] + (" (256 MB)" if des.startswith("B:") else (" (1769 MB)" if "fast" in des else "")))
        axes[1].bar(x + (k - 1) * w, s.gCO2, w, color=col)
    for ax, yl in zip(axes, ["Cost per day (USD)", "gCO$_2$e per day (log)"]):
        ax.set_xticks(x); ax.set_xticklabels([s.replace(" - ", "\n") for s in sc], fontsize=7); ax.set_ylabel(yl)
    axes[1].set_yscale("log"); axes[0].legend(fontsize=6.5)
    fig.tight_layout(); fig.savefig(f"{F}/fig_designs.png"); plt.close(fig)


# ---------------------------------------------------------------- Fig 6 break-even
def fig_breakeven():
    d = pd.read_csv(f"{R}/exp5_breakeven.csv"); cx = json.load(open(f"{R}/exp5_crossovers.json"))
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    ax = axes[0]; ax.loglog(d.req_per_day, d.cost_A, color=C["A"], label="Design A (sized for peak, min 2)"); ax.loglog(d.req_per_day, d.cost_B, color=C["B"], label="Design B (Lambda 256 MB)")
    if cx["cost"]: ax.axvline(cx["cost"], color="k", ls=":", lw=1); ax.text(cx["cost"] * 1.1, d.cost_B.min() * 3, f"cost\ncrossover\n~{cx['cost']/1e6:.1f}M/day", fontsize=6.5)
    ax.set_xlabel("Requests per day"); ax.set_ylabel("Cost per day (USD)"); ax.legend(fontsize=6.5)
    ax = axes[1]; ax.loglog(d.req_per_day, d.gCO2_A, color=C["A"], label="Design A")
    for f, ls in [("1.0", "-"), ("1.5", "--"), ("2.0", ":")]:
        ax.loglog(d.req_per_day, d[f"gCO2_B_idle{f}"], color=C["B"], ls=ls, label=f"Design B, idle factor {f}")
    if cx["gCO2_idle2.0"]:
        ax.axvline(cx["gCO2_idle2.0"], color="k", ls=":", lw=1)
        ax.text(cx["gCO2_idle2.0"] * 0.8, d["gCO2_B_idle1.0"].min() * 3, f"carbon crossover\n(idle factor 2.0)\n~{cx['gCO2_idle2.0']/1e6:.0f}M/day", fontsize=6.5, ha="right")
    ax.set_xlabel("Requests per day"); ax.set_ylabel("gCO$_2$e per day"); ax.legend(fontsize=6.5)
    fig.tight_layout(); fig.savefig(f"{F}/fig_breakeven.png"); plt.close(fig)


# ---------------------------------------------------------------- Fig 7 scheduler
def fig_sched():
    d = pd.read_csv(f"{R}/exp4_sweeps.csv"); fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.5))
    for ax, (sw, xl) in zip(axes, [("window_h", "Flexibility window (h)"), ("forecast_err", "Forecast error (sd)"), ("grid_variability", "Grid variability (x baseline)")]):
        for job, col, mk in zip(d.job.unique(), [C["B"], C["A"]], ["o", "s"]):
            s = d[(d.job == job) & (d["sweep"] == sw)]; ax.plot(s.x, s.saving_pct, color=col, marker=mk, ms=3.5, label=job)
        ax.set_xlabel(xl); ax.set_ylabel("CO$_2$e saving vs run-now (%)")
    axes[0].legend(fontsize=6, loc="upper left")
    fig.tight_layout(); fig.savefig(f"{F}/fig_scheduler.png"); plt.close(fig)


# ---------------------------------------------------------------- new figures (v2)
sys.path.insert(0, os.path.join(ROOT, "src"))
import grid as G, scheduler as S


def fig_grid():
    h = np.arange(24); fig, ax = plt.subplots(figsize=(7.0, 2.6))
    cols = {"ap-northeast-1": C["A"], "us-east-1": "#d98a1c", "us-west-2": C["B"], "eu-north-1": C["G"]}
    names = {"ap-northeast-1": "Tokyo", "us-east-1": "N. Virginia", "us-west-2": "Oregon", "eu-north-1": "Stockholm"}
    for r, c in cols.items():
        utc = (h - 8) % 24; ax.plot(h, G.profile_local(r, (utc + G.REGIONS[r][0]) % 24), color=c, marker="o", ms=3, label=names[r])
    ax.set_yscale("log"); ax.set_xlabel("Local hour (UTC+8, student time zone)"); ax.set_ylabel("Assumed intensity (gCO$_2$e/kWh, log)")
    ax.legend(ncol=4, fontsize=7, loc="center", bbox_to_anchor=(0.5, 0.5)); fig.tight_layout(); fig.savefig(f"{F}/fig_grid.png"); plt.close(fig)


def fig_sensitivity():
    d = pd.read_csv(f"{R}/exp6_sensitivity.csv"); b = d.iloc[0]; d = d.iloc[1:].copy()
    d = d.assign(span=(d.co2_ratio_high / d.co2_ratio_low).apply(lambda x: abs(np.log(x)))).sort_values("span").reset_index(drop=True)
    labels = [f"{n}: {l} / {h_}" for n, l, h_ in zip(d.parameter, d.low, d.high)]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4))
    for k, (ax, (lo, hi, base, xl)) in enumerate(zip(axes, [("co2_ratio_low", "co2_ratio_high", b.co2_ratio_low, "Emissions ratio B / A (log)"),
                                                           ("cost_ratio_low", "cost_ratio_high", b.cost_ratio_low, "Cost ratio B / A (log)")])):
        for i, r in d.iterrows():
            ax.plot([r[lo], r[hi]], [i, i], color="#7f9fcf", lw=5, solid_capstyle="butt", zorder=2)
            ax.plot(r[lo], i, "o", color=C["G"], ms=4, zorder=3); ax.plot(r[hi], i, "s", color=C["A"], ms=4, zorder=3)
        ax.axvline(base, color="k", ls="--", lw=1); ax.axvline(1.0, color="#999", ls=":", lw=1)
        ax.set_xscale("log"); ax.set_xlabel(xl); ax.set_yticks(range(len(d)))
        if k == 0: ax.set_yticklabels(labels, fontsize=6)
        else: ax.set_yticklabels([]); ax.tick_params(left=False)
    axes[0].set_title("green circle = low value, red square = high value", fontsize=7); axes[1].set_title("dashed = baseline, dotted = parity (B = A)", fontsize=7)
    fig.tight_layout(); fig.savefig(f"{F}/fig_sensitivity.png"); plt.close(fig)


def fig_flash():
    t = json.load(open(f"{R}/exp8_tails.json")); fig, ax = plt.subplots(figsize=(7.0, 2.8))
    sty = {"A: 2 x t3.medium": (C["A"], "-"), "A: 7 x t3.medium": ("#d98a1c", "-"), "B: Lambda 256 MB, cold 0.3 s": (C["B"], "-"),
           "B: Lambda 256 MB, cold 1.0 s": (C["B"], "--"), "B-fast: Lambda 1769 MB, cold 0.3 s": (C["F"], "-")}
    for k, (c, ls) in sty.items():
        y = np.array(t[k]) * 1000; n = len(y); ccdf = 1 - np.arange(n) / n
        ax.step(y, ccdf, where="post", color=c, ls=ls, label=k)
    ax.axvline(100, color="k", ls=":", lw=1); ax.text(105, 0.5, "100 ms target", fontsize=6.5)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("Latency (ms)"); ax.set_ylabel("Share of burst requests slower than x")
    ax.legend(fontsize=6.5, loc="lower left"); fig.tight_layout(); fig.savefig(f"{F}/fig_flash.png"); plt.close(fig)


def fig_sched_example():
    act = G.actual_series("ap-northeast-1", 12, seed=3); fc = G.forecast_from(act, 0.06, seed=14)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
    for ax, (ttl, ready, dur, dl) in zip(axes, [("Nightly grading (2 h, ready 23:00, window 9 h)", 23, 2, 9), ("Video transcoding (8 h, ready 18:00, window 24 h)", 18, 8, 24)]):
        now = 5 * 24 + (ready - 8) % 24; s = S.best_start(fc, now, dur, dl); x = np.arange(now - 8, now + 34)
        ax.plot(x, act[x], color=C["K"], lw=1.2, label="actual"); ax.plot(x, fc[x], color="#aaa", lw=1, ls="--", label="forecast")
        ax.axvspan(now, now + dl, color="#eef3fa", zorder=0); ax.axvspan(now, now + dur, color=C["A"], alpha=.35, label="run now")
        ax.axvspan(s, s + dur, color=C["G"], alpha=.45, label="scheduled")
        ax.set_xticks(x[::6]); ax.set_xticklabels([f"{(int(v) + 8) % 24:02d}:00" for v in x[::6]], fontsize=6.5)
        ax.set_title(ttl, fontsize=7); ax.set_xlabel("Local time (UTC+8)"); ax.set_ylabel("gCO$_2$e / kWh (Tokyo, assumed)")
    axes[0].legend(fontsize=6, loc="upper right"); fig.tight_layout(); fig.savefig(f"{F}/fig_sched_example.png"); plt.close(fig)


if __name__ == "__main__":
    fig_arch(); fig_pipeline(); fig_memory(); fig_hourly(); fig_designs(); fig_breakeven(); fig_sched(); fig_grid(); fig_sensitivity(); fig_flash(); fig_sched_example(); print(sorted(os.listdir(F)))
