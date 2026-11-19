# -*- coding: utf-8 -*-
import os, json
import pandas as pd
from docx_lib import *
from content_b import excerpt

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def f(x, d=2): return f"{x:,.{d}f}"


def part_c(add, fig, tab):
    # ============================================================ 7 Results
    add(p_h1("Results and Evaluation"))
    add(p_body("This section reports eight experiments: memory and architecture (7.1), the design comparison (7.2), regions (7.3), scheduling (7.4), break-even (7.5), sensitivity (7.6), stronger baselines (7.7) and a flash crowd (7.8). Unless stated otherwise, figures come from the model of Section 6 and the parameters of @@T:t_param@@; they are estimates, not measurements on AWS."))
    # ---------------- 7.1
    add(p_h2("7.1 Experiment 1: memory size and CPU architecture"))
    add(p_body("Memory size was swept from 128 MB to 3,008 MB for two workloads on x86 and arm64: the I/O-dominated API mix (about 4.3 ms of CPU and 10.6 ms of I/O wait per request) and a CPU-dominated batch grading call (1.5 s of CPU). "
               "@@T:t_mem@@ and @@F:fig_memory@@ show opposite behaviour. For the API, a larger memory buys little: the duration falls from 40.4 ms at 256 MB to 14.9 ms at 1,769 MB, but the cost per million requests rises from USD 0.337 to 0.546 (+62 %), "
               "because the fixed I/O wait is billed at a higher memory price. For the CPU-dominated call, cost and energy stay almost flat from 256 MB to 1,769 MB (USD 34.9–35.9 per million) while the duration falls from 10.4 s to 1.55 s, "
               "so the extra speed is almost free. Above 1,769 MB the duration no longer improves, because the single-threaded code cannot use a second vCPU, but the cost rises by 70 % (USD 60.9 per million at 3,008 MB) and the energy from 1.37 to 2.32 Wh per thousand calls. "
               "Arm64 lowered the total cost by 8.5–15.7 % for the API mix (the fixed request fee dilutes the 20 % duration discount) and by about 19.9 % for the CPU-dominated call. Energy follows cost closely because both grow with allocated memory multiplied by time."))
    tab("t_mem", "Memory sweep on arm64 (cost excludes the API gateway).",
        ["Workload", "Memory (MB)", "Duration (ms)", "Cost (USD per 1M req.)", "Energy (Wh per 1,000 req.)"],
        [["API mix (I/O-dominated)", "256", "40.4", "0.337", "0.005"], ["", "1,769", "14.9", "0.546", "0.013"], ["", "3,008", "14.9", "0.788", "0.022"],
         ["Batch grading (1.5 s CPU)", "256", "10,415", "34.92", "1.329"], ["", "1,769", "1,550", "35.90", "1.367"], ["", "3,008", "1,550", "60.91", "2.324"]],
        [2700, 1300, 1500, 1800, 1714], align=["left", "center", "center", "center", "center"])
    fig("fig_memory", "Memory sweep for the two workloads. Lines show cost on x86 and arm64 (left axis); the dashed line shows the duration on arm64 (right axis, logarithmic).")
    add(p_body("Two practical rules follow. I/O-bound request handlers should use the smallest memory that meets the latency target. CPU-bound functions should be raised to about 1,769 MB (one vCPU) and not further unless the code is multi-threaded."))
    # ---------------- 7.2
    add(p_h2("7.2 Experiment 2: Design A versus Design B"))
    add(p_body("Both designs were simulated for a normal campus day, a campus exam day and a large exam day. The daily pattern on the normal day is as follows. Design A emits about 3 g CO_{2}e every hour of the day because its two instances draw their idle power "
               "regardless of traffic, whereas the emissions of Design B follow the request curve, from about 0.001 g in the early morning to about 0.06 g at the evening peak. The mean CPU utilisation of Design A is only 0.4 % on a normal day (peak 0.7 %), 1.1 % on the campus exam day (peak 6.5 %) and 6.6 % on the large exam day (peak 39 %)."))
    add(p_body("@@T:t_design@@ gives the daily totals. On the normal campus day Design B costs USD 0.40 against USD 2.73 (−85 %) and emits 0.70 g against 77.1 g (−99 %). On the campus exam day the figures are USD 1.21 against 2.73 (−56 %) and 2.1 g against 78.0 g (−97 %). "
               "On the large exam day, with 5.4 million requests, Design B emits 12.8 g against 85.3 g (−85 %) but is now more expensive: USD 7.24 against 2.73 (+165 %). "
               "Both designs met the latency target in every scenario and Design A never queued, because even the large exam day needs less than 40 % of its four vCPUs at the peak. "
               "The 95th-percentile latency of Design B at 256 MB is 73.5 ms against 20.9 ms for Design A, dominated by the login call, which receives only 0.14 vCPU. "
               "A variant at 1,769 MB (B-fast) matches Design A’s latency for 17 % more cost than B at 256 MB on the normal day and 2.5 times its emissions, still 98 % below Design A. "
               "In this steady-traffic simulation cold starts affect at most 0.002 % of requests; Experiment 8 shows that this changes completely in a flash crowd."))
    tab("t_design", "Daily cost, estimated energy, emissions and latency of the designs.",
        ["Scenario", "Design", "Cost (USD/day)", "Energy (Wh/day)", "CO_{2}e (g/day)", "p95 (ms)"],
        [["Campus, normal day (300k req.)", "A: 2 × t3.medium", "2.73", "167.2", "77.1", "20.9"], ["", "B: Lambda 256 MB", "0.40", "1.5", "0.70", "73.5"], ["", "B-fast: Lambda 1,769 MB", "0.47", "3.9", "1.78", "20.9"],
         ["Campus, exam day (900k req.)", "A: 2 × t3.medium", "2.73", "169.3", "78.0", "20.9"], ["", "B: Lambda 256 MB", "1.21", "4.8", "2.13", "73.5"], ["", "B-fast: Lambda 1,769 MB", "1.44", "13.5", "5.97", "20.9"],
         ["Large, exam day (5.4M req.)", "A: 2 × t3.medium", "2.73", "185.8", "85.3", "20.9"], ["", "B: Lambda 256 MB", "7.24", "28.8", "12.76", "73.5"], ["", "B-fast: Lambda 1,769 MB", "8.66", "81.0", "35.82", "20.9"]],
        [2250, 2100, 1150, 1250, 1150, 1114], align=["left", "left", "center", "center", "center", "center"])
    # ---------------- 7.3
    add(p_h2("7.3 Experiment 3: choice of region"))
    add(p_body("Running the same workload in other regions changes only the grid intensity in the model (@@T:t_region@@). Relative to Tokyo, the Virginia and Oregon regions lower the emissions of Design B by 16 % and 28 %, and Stockholm by 95 %. "
               "The same percentages apply to Design A, whose absolute emissions are about a hundred times higher. Moving the interactive API abroad would, however, add network latency for students in China and may conflict with data-protection rules, "
               "so a change of region is attractive mainly for batch jobs, which are examined next."))
    tab("t_region", "Daily emissions of the normal campus day by region (assumed, rounded intensities).",
        ["Region", "Mean intensity (g/kWh)", "Design A (g/day)", "Design B (g/day)", "Design B vs. Tokyo"],
        [["Tokyo (ap-northeast-1)", "461", "77.1", "0.70", "–"], ["N. Virginia (us-east-1)", "375", "62.7", "0.59", "−15.6 %"],
         ["Oregon (us-west-2)", "315", "52.6", "0.50", "−28.3 %"], ["Stockholm (eu-north-1)", "25", "4.1", "0.04", "−94.7 %"]],
        [2500, 1800, 1500, 1500, 1714], align=["left", "center", "center", "center", "center"])
    # ---------------- 7.4
    add(p_h2("7.4 Experiment 4: carbon-aware scheduling of batch jobs"))
    add(p_body("The scheduler was evaluated over 60 simulated days with day-to-day fluctuation in the grid and a forecast error of 6 %. Four strategies were compared: running immediately in Tokyo, shifting in time within the deadline window, moving to the cleanest region without waiting, and combining both (@@T:t_sched@@). "
               "Temporal shifting alone saves 4.4 % for the nightly grading job (9 h window, mean delay 4.5 h) and 16.5 % for the transcoding job (24 h window, mean delay 14.1 h). Moving the jobs to Stockholm saves 93.5 % and 88.2 %, and combining both adds almost nothing, "
               "because the regional difference dominates the hourly difference. The residual emissions of the regional strategy are largely caused by the data transfer: for the transcoding job, moving 20 GB accounts for about 9 g of the 17 g that remain, "
               "so transfer volume must be included in any regional decision. As the regional strategy is only permissible for data that may leave the home region, it is limited here to anonymised inputs."))
    tab("t_sched", "Emissions per job under four scheduling strategies (mean ± standard deviation over 60 days).",
        ["Job", "Strategy", "CO_{2}e per job (g)", "Saving (%)", "Mean delay (h)"],
        [["Nightly grading (8 vCPU × 2 h, 9 h window)", "Run immediately", "35.0 ± 2.4", "–", "0"], ["", "Shift in time", "33.5 ± 2.4", "4.4", "4.5"], ["", "Move region", "2.28 ± 0.12", "93.5", "0"], ["", "Time and region", "2.26 ± 0.12", "93.6", "2.7"],
         ["Video transcoding (8 vCPU × 8 h, 24 h window)", "Run immediately", "143.5 ± 8.6", "–", "0"], ["", "Shift in time", "119.9 ± 7.6", "16.5", "14.1"], ["", "Move region", "17.0 ± 0.8", "88.2", "0"], ["", "Time and region", "16.9 ± 0.8", "88.3", "6.3"]],
        [3000, 1800, 1700, 1250, 1264], align=["left", "left", "center", "center", "center"])
    add(p_body("@@F:fig_sched_example@@ shows what a single decision looks like. On the example day the grading job, which became ready at 23:00, was postponed by two hours to 01:00; with the actual (not the forecast) intensity this was 0.7 % worse than running immediately, "
               "because the forecast was slightly wrong. The transcoding job, ready at 18:00, was postponed by 14 hours to 08:00 and its actual mean intensity was 21 % lower. Individual decisions can therefore lose; the benefit is a statistical one that appears in the average over many days, as in @@T:t_sched@@."))
    fig("fig_sched_example", "Example scheduling decision on one simulated day (Tokyo). The pale band is the admissible window, red marks the run-now slot and green the scheduled slot.")
    add(p_body("@@F:fig_scheduler@@ shows how the saving of temporal shifting depends on three factors. First, the window: nothing can be saved until the window exceeds the job duration; for the 2-hour grading job the saving is 4.4 % at 9 h, 12.4 % at 12 h and about 18–19 % at 18 h or more, "
               "while the 8-hour transcoding job needs a window of about 18 h to reach 10 % and 24 h to reach 16.5 %. Second, forecast accuracy: with a 24 h window, the saving of the grading job falls from 19.3 % with a perfect forecast to 17.0 % at 10 % error and 8.4 % at 40 % error. "
               "Third, the variability of the grid: scaling the daily swing of the synthetic profile by 0, 1 and 2 changes the saving of the grading job from 6.2 % to 18.5 % and 35.5 %. These results agree in direction with the literature [[wiesner]], but their size depends on the assumed profile and must be re-estimated with real intensity data."))
    fig("fig_scheduler", "Saving of temporal shifting versus run-now as a function of the flexibility window (left), the forecast error (centre, 24 h window) and the grid variability (right, 24 h window).")
    # ---------------- 7.5
    add(p_h2("7.5 Experiment 5: break-even analysis"))
    add(p_body("To find out whether the advantage of Design B is a feature of small platforms, the daily request volume was varied from 10^{4} to 10^{9}. Design A is resized to the peak at each volume (at least two instances). @@F:fig_breakeven@@ shows the result. "
               "In cost, the lines cross at about 2.4 million requests per day (an average of 27 requests per second). At 10^{8} requests per day Design A needs 8 instances (USD 8.72 per day) against USD 134 for Design B, and at 10^{9} requests it needs 80 instances (USD 80.6) against USD 1,340. "
               "The API gateway fee, assumed at USD 1.00 per million requests, makes up 75 % of the per-request cost of Design B; without it, the crossover would move to roughly 8 million requests per day."))
    add(p_body("In emissions, Design B stays below Design A over the entire range if the provider-side idle overhead is ignored (factor 1.0) or set to 1.5. If the overhead is set to 2.0, that is, if the provider attributes twice the modelled energy to each Lambda request, the lines cross at about 75 million requests per day. "
               "The carbon advantage of serverless therefore rests on avoiding idle capacity: it is robust for small and medium platforms and weakens only at a scale where a VM fleet would run at high utilisation. "
               "Because the true overhead is not observable by the customer, this factor is the largest source of uncertainty in the comparison."))
    fig("fig_breakeven", "Break-even analysis. Left: cost per day versus requests per day. Right: emissions per day for Design A and for Design B under idle overhead factors of 1.0, 1.5 and 2.0 (dotted line: crossover for factor 2.0).")
    # ---------------- 7.6
    add(p_h2("7.6 Experiment 6: sensitivity analysis"))
    add(p_body("The conclusions rest on assumed parameters, so each of ten parameters was varied one at a time over a plausible range for the campus normal day, and the ratio of Design B to Design A was recomputed. @@F:fig_sensitivity@@ shows the result. "
               "The baseline ratios are 0.147 for cost (B costs 14.7 % of A) and 0.0091 for emissions (B emits 0.9 % of A, a factor of 110 less)."))
    add(p_body("Three results stand out. First, **emissions**: in no single-parameter case does the ratio exceed 0.086, so Design B stays at least 11.7 times lower. The largest effects are the daily volume (30,000 to 3 million requests: 0.0009 to 0.086) "
               "and the provider idle overhead (factor 3 triples the ratio to 0.027); the power coefficients and the Lambda utilisation move the ratio by less than a factor of two. "
               "Second, **cost**: the ratio exceeds 1 only when the daily volume is ten times larger (3 million requests, ratio 1.47), and it is dominated by the API gateway price, which alone moves it between 0.037 and 0.257. "
               "Third, the model’s own uncertain inputs (I/O wait, cold-start share) hardly matter: doubling the I/O wait changes the cost ratio by about 2.5 %."))
    fig("fig_sensitivity", "Sensitivity of the ratio B/A to ten parameters. Bars span the low and high values (green circle low, red square high); the dashed line is the baseline and the dotted line marks parity.")
    add(p_body("To test the conclusions against combined uncertainty, two extreme parameter sets were evaluated. In a deliberately pessimistic case for Design B (Lambda utilisation 100 %, idle overhead factor 3, CPU time and I/O wait doubled, 2 % cold starts, and power coefficients that lower the energy of Design A), "
               "Design B still emits only 6.7 % of Design A (3.9 g against 58.5 g) and costs 16 % of it (USD 0.45 against 2.73). In the optimistic case the ratios are 0.4 % and 14 %. The qualitative conclusion for the campus scale is therefore robust to the assumptions tested, "
               "while the conclusion for large platforms is not (daily volume is the dominant parameter)."))
    # ---------------- 7.7
    add(p_h2("7.7 Experiment 7: stronger VM baselines"))
    add(p_body("A fair comparison should not pit serverless against the weakest possible VM setup. Experiment 7 therefore adds three cheaper variants of Design A: one-year reserved t3.medium instances (USD 0.029/h), Arm-based t4g.medium instances on demand (USD 0.0336/h) "
               "and reserved t4g.medium instances (USD 0.0196/h) [[t3price,t4gprice]]. The emissions of the VM variants are kept equal to Design A’s, which is conservative for the Arm variants, because the CCF method has a lower power coefficient for Graviton processors that was not applied [[ccf]]. "
               "@@T:t_base@@ gives the daily costs."))
    e7 = pd.read_csv(os.path.join(RES, "exp7_baselines.csv"))
    names = ["A: t3.medium on-demand", "A-RI: t3.medium 1-yr reserved", "A-arm: t4g.medium on-demand", "A-arm-RI: t4g.medium 1-yr reserved", "B: Lambda arm64 256MB", "B-fast: Lambda arm64 1769MB"]
    scs = ["Campus - normal day", "Campus - exam day", "Large - exam day"]
    rows = []
    for nme in names:
        r = [nme.replace("arm64 ", "arm64 ").replace("256MB", "256 MB").replace("1769MB", "1,769 MB")]
        for sc in scs:
            c = e7[(e7.design == nme) & (e7.scenario == sc)].iloc[0]; r.append(f"{c.cost_usd:.2f}")
        g = e7[(e7.design == nme) & (e7.scenario == scs[0])].iloc[0].gCO2; r.append(f"{g:.1f}" if g > 10 else f"{g:.2f}")
        rows.append(r)
    tab("t_base", "Daily cost (USD) of stronger VM baselines and emissions on the normal campus day.",
        ["Design", "Normal day", "Campus exam day", "Large exam day", "CO_{2}e normal day (g)"], rows,
        [3500, 1250, 1450, 1450, 1364], align=["left", "center", "center", "center", "center"])
    add(p_body("Even the strongest baseline, two reserved Arm instances, costs USD 1.67 per day (including the load balancer) against USD 0.40 for Design B on the normal day, so Design B remains 76 % cheaper at campus scale and 28 % cheaper on the campus exam day. "
               "The cost crossover moves down accordingly: against reserved Arm instances, Design B stops being cheaper at about 1.3 million requests per day instead of 2.4 million. For large platforms the VM option is clearly cheaper "
               "(USD 1.67 against 7.24 on the large exam day, 4.3 times less), which is the expected economics of high utilisation. The carbon comparison is not changed by the price variants. For the Arm variants the lower Graviton power coefficient would reduce the emissions of Design A, but even if the Arm instances needed only half the energy of the x86 fleet, "
               "Design B would still emit about 2 % of their emissions (ratio 0.018), so the emission advantage at campus scale does not depend on the baseline chosen."))
    # ---------------- 7.8
    add(p_h2("7.8 Experiment 8: exam-start flash crowd"))
    add(p_body("The average-rate analysis hides the moment that matters most to students: the start of an exam. Experiment 8 adds 20,000 requests (half logins, half quiz submissions) within 10 seconds at 14:00:00 to the campus exam day. "
               "This is a rate of 2,000 requests per second and a CPU demand of 12.7 vCPUs. Besides Design A with two instances and Design B at two memory sizes, a larger VM fleet was added; the smallest fleet that kept the burst latency within the target was found to be seven instances (six instances still gave a 567 ms 99th percentile and 88 % of burst requests above 100 ms). @@T:t_flash@@ and @@F:fig_flash@@ show the outcome."))
    e8 = pd.read_csv(os.path.join(RES, "exp8_flash_crowd.csv"))
    lab = {"A: 2 x t3.medium": "A: 2 × t3.medium", "A: 7 x t3.medium": "A: 7 × t3.medium", "B: Lambda 256 MB, cold 0.3 s": "B: Lambda 256 MB, cold start 0.3 s",
           "B: Lambda 256 MB, cold 1.0 s": "B: Lambda 256 MB, cold start 1.0 s", "B: Lambda 256 MB, cold 0.3 s, keep-alive 1 min": "B: Lambda 256 MB, keep-alive 1 min", "B-fast: Lambda 1769 MB, cold 0.3 s": "B-fast: Lambda 1,769 MB"}
    rows = []
    for r in e8.itertuples():
        rows.append([lab[r.design], f"{r.slo_viol_burst_pct:.1f}", f"{r.p50_ms:,.0f}", f"{r.p99_ms:,.0f}", f"{int(r.cold_starts):,}", f"{r.daily_cost_usd:.2f}"])
    tab("t_flash", "Flash crowd of 20,000 requests in 10 seconds (burst-window latencies; cost for the whole day).",
        ["Design", "Over 100 ms (%)", "p50 (ms)", "p99 (ms)", "Cold starts", "Cost (USD/day)"], rows,
        [3300, 1250, 1050, 1150, 1100, 1164], align=["left", "center", "center", "center", "center", "center"], sz=17)
    fig("fig_flash", "Complementary latency distribution of the requests in the flash-crowd window (logarithmic axes). Design A with two instances builds a queue lasting about 20 seconds.")
    add(p_body("The result is stark. The two-instance fleet, perfectly adequate for the daily average, cannot absorb the burst: 99.6 % of the burst requests exceed 100 ms, the median latency is 10.8 s and the worst request waits 21.7 s, because 12.7 vCPUs of demand arrive at a 4-vCPU fleet. "
               "Over the whole day, 2.4 % of all requests violate the target because of this one event. Sizing the fleet for the burst (seven instances) removes the problem entirely (99th percentile 31 ms), but the daily cost rises from USD 2.73 to 7.72, "
               "which is 6.2 times the cost of Design B on the same day (USD 1.24) and means that most of the capacity is idle for the rest of the day."))
    add(p_body("Design B absorbs the burst because Lambda creates environments as requests arrive. The price is cold starts: 690 of the 20,516 burst requests (3.4 %) found no warm environment and took 300 ms longer, so the 99th percentile equals the cold-start time (374 ms) and 3.4 % of the burst requests miss the 100 ms target. "
               "With a heavier package and a 1-second cold start the figure rises to 2,049 cold starts (10.0 %) and a 99th percentile of 1,074 ms. A larger memory size helps a little (564 cold starts, 2.75 %) because every request finishes sooner and environments are reused earlier. "
               "A shorter keep-alive made no difference in this scenario because the pool was already warm from the preceding traffic. Cold starts occur in clusters: the first 0.3 seconds of the burst create several hundred environments at once."))
    add(p_body("Neither design is perfect. For Design B the remedies are a small package, provisioned concurrency for the exam start (at additional cost) and a quota check, since the burst needed several hundred concurrent executions; the simulation models neither concurrency limits nor a platform ramp-up rate. "
               "For Design A they are scheduled scaling before announced exams or a larger fleet. The choice between the designs is, above all, a choice of how to pay for burst capacity."))
    # ---------------- 7.9
    add(p_h2("7.9 Synthesis of the findings"))
    add(p_body("@@T:t_syn@@ condenses the evidence by research question."))
    tab("t_syn", "Summary of the main findings.",
        ["RQ", "Finding", "Evidence"],
        [["RQ1", "At campus scale Design B is 85 % cheaper and emits 99 % less than two VMs, with the latency target met", "Sections 7.2, 7.7; sensitivity ratio ≤ 0.086 in all tested cases"],
         ["RQ1", "The cost advantage ends at about 2.4M requests/day (1.3M against reserved Arm VMs); the carbon advantage lasts to much larger volumes", "Sections 7.5, 7.7"],
         ["RQ1", "A static VM fleet fails an exam-start flash crowd unless sized about 3.5 times larger; Lambda copes at the price of 3.4 % cold starts", "Section 7.8"],
         ["RQ2", "Memory: smallest meeting the latency target for I/O-bound code, about 1,769 MB for CPU-bound code; Arm64 saves up to 20 %", "Section 7.1"],
         ["RQ2", "Daily volume, provider idle overhead and API gateway price dominate; power coefficients and I/O wait hardly matter", "Section 7.6"],
         ["RQ3", "Shifting in time saves 4–17 % (up to 19 % with long windows); moving to a clean region saves 88–94 % for anonymised data", "Section 7.4"],
         ["RQ3", "Savings depend on window length, forecast accuracy and grid variability; single decisions can lose", "Section 7.4 (example day)"]],
        [700, 5000, 3314], align=["center", "left", "left"], sz=17)

    # ============================================================ 8 Discussion
    add(p_h1("Discussion"))
    add(p_h2("8.1 Answers to the research questions"))
    add(p_body("**RQ1.** Yes for the campus scale studied: the serverless design meets the latency target and is cheaper and much lower in estimated emissions, with a robust margin. The answer is conditional on volume (the cost advantage ends at a few million requests a day), on burst handling (cold starts) "
               "and on availability design (the composite commitment of an API gateway plus Lambda is slightly below 99.9 % unless the gateway is bypassed or clients retry). **RQ2.** The configuration choices that matter are the memory size, which should follow the CPU-versus-I/O character of the code, "
               "and the CPU architecture, where Arm64 is a free 20 % on the duration charge. The model assumptions that matter are daily volume, provider idle overhead and the gateway price; the technical ones such as power coefficients matter much less. "
               "**RQ3.** Carbon-aware scheduling is worthwhile for jobs with long windows and clearly variable grids, and it is most effective as a regional choice, but its size is the least certain result because it depends on grid data that were synthetic here."))
    add(p_h2("8.2 Evaluation against the requirements"))
    add(p_body("@@T:t_eval@@ summarises how the designs fare against the evaluation criteria of the assignment. Both meet the latency and availability targets in the steady-state simulation. The difference lies in cost structure, emissions and burst behaviour: Design A pays for idle capacity, Design B pays per use and for cold starts."))
    tab("t_eval", "Evaluation of the two designs.",
        ["Criterion", "Design A (VMs)", "Design B (serverless)"],
        [["Scalability", "Rule-based; handles the large exam day at 39 % peak utilisation but needs about 3.5 times the fleet for a flash crowd", "Automatic; absorbs a flash crowd; limited by account concurrency quotas"],
         ["Availability", "99.93 % composite commitment; two zones and health checks", "99.89 % via API gateway, 99.94 % via function URL; fewer components to operate"],
         ["Performance", "p95 20.9 ms; queueing under bursts beyond fleet capacity", "p95 73.5 ms at 256 MB, 20.9 ms at 1,769 MB; 3.4 % cold starts in a burst"],
         ["Security", "More surface to patch (OS, runtime, SSH, AMIs)", "Smaller surface; IAM policy per function becomes the main control; denial-of-wallet risk"],
         ["Cost", "USD 1.67–2.73/day at any campus volume; cheaper above 1.3–2.4M requests/day", "USD 0.40–7.24/day in the scenarios; cheaper below 1.3–2.4M requests/day"],
         ["Carbon", "77–85 g/day, dominated by idle power", "0.7–12.8 g/day (−85 % to −99 %); sensitive to the idle-overhead assumption"]],
        [1500, 3757, 3757], align=["left", "left", "left"], bold_first_col=True)
    add(p_h2("8.3 Threats to validity"))
    add(p_body("The results must be read within the limits summarised in @@T:t_valid@@. The most important one is the first: no workload was run on an AWS account, and energy is estimated rather than metered."))
    tab("t_valid", "Threats to validity and how they were handled.",
        ["Type", "Threat", "Handling and effect"],
        [["Construct", "Energy and carbon are modelled, not measured; only operational, location-based emissions are covered [[ccf,ccft]]", "Coefficients from the CCF method; embodied emissions excluded and stated; SCI-style unit"],
         ["Construct", "Shared components (database, object storage, CDN, data transfer, NAT) are excluded", "Same in both designs; RDS idle energy and NAT would add to Design A, so the exclusion favours A"],
         ["Internal", "Assumed I/O wait, overhead, cold start, batch sizes and grid profiles", "Listed in the parameter table; ten parameters tested one at a time and in two combinations"],
         ["Internal", "Burstable-CPU credits of t3 instances ignored; Graviton power advantage not credited", "Both are conservative for Design B or neutral; Arm baselines added in Experiment 7"],
         ["Internal", "Cold starts and environment recycling simplified; no platform ramp-up limits", "Flash-crowd experiment varies cold-start time and keep-alive; quotas flagged as a risk"],
         ["External", "One university scenario, one provider, one region family, a single Python workload", "Volume swept over five orders of magnitude; findings for other settings need re-testing"],
         ["Conclusion", "One random seed; scheduling over 60 simulated days; CPU timings from one machine", "Standard deviations reported; timings affect all results proportionally"]],
        [1200, 4200, 3614], align=["left", "left", "left"], sz=17, bold_first_col=True)
    add(p_h2("8.4 Practical guidelines"))
    add(p_body("For a university platform of this size the results support six practices: serve the interactive tier on a serverless platform at the smallest memory that meets the latency target, on Arm64; "
               "remove avoidable links such as the API gateway from the request path and let clients retry idempotent calls; prepare for announced exams with provisioned concurrency or pre-scaling, a quota check and burst load tests; "
               "give delay-tolerant jobs 12–24 hours of flexibility and schedule them by forecast, expecting day-to-day variation; move jobs to another region only for anonymised data and after counting the transfer; "
               "and track emissions per 1,000 requests as an SCI-style indicator [[scispec]] together with cost, re-running the break-even analysis when the platform grows by an order of magnitude."))
    add(p_h2("8.5 Social, ethical and regulatory considerations"))
    add(p_body("**Data protection.** Student records are personal data; rules restricting cross-border transfers can forbid exactly the regional shifting that gives the largest saving, so the design limits it to anonymised inputs. "
               "**Rebound effects.** Lower cost per request can increase usage, so sustainability policy should look at absolute emissions as well as the rate per request. "
               "**Fairness.** Cold starts and queueing hit students at the worst moment; an architecture that is greener on average but unreliable at exam start would be educationally unacceptable, which is why the flash crowd is part of the evaluation. "
               "**Transparency.** Because the figures are estimates, they should be reported with method and uncertainty to avoid false precision and “greenwashing”; the SCI practice of declaring boundary and method [[scispec]] is followed for this reason."))
    add(p_h2("8.6 Future work"))
    add(p_body("The next steps are to deploy both designs with the supplied template and load test and replace the simulated durations by CloudWatch measurements; to replace the synthetic grid profiles by a year of real hourly data and forecasts for several regions; "
               "to add Fargate and EKS and include the network and database tiers in the boundary; to evaluate provisioned concurrency against real Lambda scaling limits; and to include embodied emissions and market-based accounting."))

    # ============================================================ 9 Conclusion
    add(p_h1("Conclusion"))
    add(p_body("This report designed and evaluated two architectures for an online education platform and treated carbon emissions as a requirement next to cost, availability and latency. "
               "For a campus of 10,000 students, a serverless design on Lambda met a 100 ms latency target while reducing daily cost by 85 % and estimated emissions by 99 % compared with two always-on VMs, because the VMs run at under 1 % utilisation on a normal day. "
               "The advantage held against stronger baselines (76 % cheaper than reserved Arm instances) and in every one-at-a-time sensitivity case (emissions at least 11 times lower). "
               "The cost advantage ends at roughly 2.4 million requests per day, mainly because of the API gateway fee, whereas the carbon advantage persists to far larger volumes unless the provider’s idle overhead is about twice what the model assumes."))
    add(p_body("Two findings qualify the headline result. The flash-crowd experiment showed that a minimal VM fleet fails at the start of an exam, whereas serverless copes but pays with cold starts for 3.4 % of the burst requests; and the availability check showed that serverless needs a deliberate design (a shorter request path, client retries) to meet 99.9 %. "
               "Memory configuration matters in opposite ways for I/O-bound and CPU-bound code, and Arm64 gives a steady 20 % price reduction on the duration charge. Carbon-aware scheduling saved 4–17 % by shifting nightly jobs in time and 88–94 % by moving them to a low-carbon region, "
               "provided the deadline window is long, the forecast is reasonable, the data may leave the region and the transfer is small."))
    add(p_body("The main limitation is that energy and grid data are modelled; deploying the prototype on AWS with real carbon-intensity data is the natural continuation. Within that limit, the report shows that sustainability can be treated as an engineering requirement with measurable indicators, explicit assumptions and tested conclusions."))
