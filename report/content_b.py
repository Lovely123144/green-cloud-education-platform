# -*- coding: utf-8 -*-
import os, re
from docx_lib import *

SRC = os.path.join(os.path.dirname(__file__), "..", "src")


def excerpt(fname, start_pat, end_pat, max_lines=40):
    lines = open(os.path.join(SRC, fname), encoding="utf-8").read().split("\n")
    i = next(k for k, l in enumerate(lines) if re.match(start_pat, l))
    j = next((k for k in range(i + 1, len(lines)) if re.match(end_pat, lines[k])), len(lines))
    out = [l for l in lines[i:j]]
    while out and not out[-1].strip(): out.pop()
    return out[:max_lines]


def part_b(add, fig, tab):
    # ============================================================ 4 Architecture
    add(p_h1("Cloud Architecture Design"))
    add(p_body("Two architectures were designed for the same requirements. Both serve the static front-end from S3 behind CloudFront and both use a managed database, so these shared components are excluded from the comparison. "
               "They differ in how the dynamic API is executed and in how batch work is handled (@@F:fig_architecture@@)."))
    fig("fig_architecture", "The two compared architectures. Design A runs the API on two always-on EC2 instances in different availability zones behind an Application Load Balancer; Design B runs it on AWS Lambda (arm64, 256 MB) behind an API gateway.")
    add(p_body("Five principles guided both designs: right-size to demand (pay and emit only for work done); keep compute stateless with state in managed services; prefer managed services to reduce patching and idle infrastructure; "
               "separate interactive from delay-tolerant work so that the latter can be scheduled by carbon and cost; and make cost and carbon observable per request (Section 4.7)."))
    add(p_h2("4.1 Design A: always-on virtual machines"))
    add(p_body("Design A places an Application Load Balancer in front of two t3.medium instances (2 vCPU, 4 GiB) in two availability zones. Each instance runs the application with gunicorn. The fleet is static and sized so that the peak CPU demand stays below 60 % utilisation, with a minimum of two instances for availability: "
               "*n* = max(2, ⌈peak vCPU demand / (0.6 × 2)⌉). Availability comes from the load balancer’s health checks and the two zones; the customer operates the operating system, the runtime and the scaling rules. "
               "The cost is nearly fixed, because instances and the load balancer are billed per hour whether or not requests arrive."))
    add(p_body("The network is a three-tier VPC over two AZs: public subnets for the load balancer, private subnets for the instances and the database, and security groups that let each tier accept traffic only from the tier in front of it. The energy and cost of network components such as a NAT gateway are not modelled, which slightly favours Design A."))
    add(p_h2("4.2 Design B: serverless with a carbon-aware batch pipeline"))
    add(p_body("Design B runs the same application code as an AWS Lambda function on arm64 with 256 MB of memory, behind an API gateway, with an on-demand database. The three routes (/login, /courses, /quiz) map to one function. Execution environments are created per request and removed after a period of inactivity, so the platform scales down to almost nothing at night and up on exam days without any scaling rules; "
               "in the simulation the pool of warm environments peaked at 6 on a normal campus day, 13 on the campus exam day and 38 on the large exam day. "
               "The memory setting was chosen by the sweep in Experiment 1: 256 MB is the smallest value for which the slowest endpoint (login) stays below the 100 ms target (128 MB would need about 135 ms)."))
    add(p_body("Throttling and reserved concurrency cap simultaneous executions, which protects the database from a stampede and limits the cost of an attack (a “denial-of-wallet” attack is the serverless counterpart of denial of service). "
               "A CloudFront distribution with a web application firewall fronts the function, which also removes the API gateway from the request path and improves the composite availability (Section 3.3); clients retry idempotent requests with a short back-off."))
    add(p_h2("4.3 Data layer"))
    add(p_body("The data model is deliberately small and is the same conceptually in both designs. Design B uses DynamoDB in on-demand capacity mode, which absorbs exam-day spikes without capacity planning; Design A uses a Multi-AZ relational database. @@T:t_data@@ lists the tables and their access patterns."))
    tab("t_data", "Data model of the platform (DynamoDB keys; the relational schema of Design A has the same entities).",
        ["Table", "Partition key", "Sort key", "Access pattern"],
        [["Users", "user_id", "–", "Read at login (strongly consistent); password hash and profile"],
         ["Courses", "catalogue_page", "course_id", "Read-mostly listing; pages also cached at the edge"],
         ["Submissions", "user_id", "quiz_id#timestamp", "Write on submit; read the student’s own submissions"],
         ["Submissions (index)", "submission_date", "submission_id", "Nightly batch reads one day of submissions"],
         ["Results", "quiz_id", "user_id", "Written by grading; read by teachers and students"]],
        [1800, 1900, 1900, 3414], align=["left", "left", "left", "left"], bold_first_col=True)
    add(p_h2("4.4 Carbon-aware batch pipeline"))
    add(p_body("Delay-tolerant jobs are handled by the pipeline in @@F:fig_pipeline@@. When a job becomes ready, EventBridge invokes a scheduler function with the job’s duration and deadline. The function obtains an hourly carbon-intensity forecast, "
               "selects the start hour inside the window [now, now + deadline − duration] that minimises the mean forecast intensity over the run (ties go to the earliest hour), and creates a one-time schedule for that hour. "
               "In the spatio-temporal variant the same search runs over several regions, with a penalty for the carbon of moving data, and only regions that are allowed for the job’s data are considered. "
               "If the forecast service is unreachable the function falls back to “run now”, so that the deadline is never endangered; a unit test confirms that the chosen start never exceeds the deadline."))
    fig("fig_pipeline", "Carbon-aware batch pipeline. A scheduler function chooses the start hour (and, for anonymised data, the region) before the batch workers run.")
    add(p_body("The selection rule is a sliding-window minimum over the admissible start hours (at most a few hundred operations for a 24-hour window):"))
    add(p_code(["function best_start(forecast, now, duration, deadline):",
                "    dur  <- ceil(duration)",
                "    last <- now + floor(deadline - dur)   # latest start meeting deadline",
                "    best <- infinity; start <- now",
                "    for s in now .. last:",
                "        m <- mean(forecast[s : s + dur])  # mean intensity over the run",
                "        if m < best: best <- m; start <- s   # ties keep earliest start",
                "    return start",
                "",
                "function best_region_start(forecasts, now, duration, deadline,",
                "                           allowed, penalty):",
                "    for each region r in allowed:",
                "        s_r     <- best_start(forecasts[r], now, duration, deadline)",
                "        score_r <- mean(forecasts[r][s_r : s_r + dur]) + penalty(r)",
                "    return the (region, start) with the lowest score"]))
    add(p_h2("4.5 Security architecture"))
    add(p_body("Security was designed against the STRIDE threat categories. @@T:t_threat@@ lists, for each category, a plausible threat on this platform and the controls in the two designs. The exam-day peak is also the moment of greatest exposure, "
               "because an attack on availability during an exam has an immediate impact on students."))
    tab("t_threat", "Threat model (STRIDE) and controls.",
        ["Threat", "Example", "Design A control", "Design B control"],
        [["Spoofing", "Guessed or stolen passwords", "PBKDF2 hashing, WAF rate limits, MFA for staff", "Same; optional managed identity provider"],
         ["Tampering", "Altered quiz answers in transit", "TLS at the load balancer, server-side validation", "TLS at CloudFront, validation in the function"],
         ["Repudiation", "Dispute about a submission time", "ALB access logs, CloudTrail", "CloudTrail, function logs, item timestamps"],
         ["Information disclosure", "Leak of student data", "Private subnets, security groups, KMS encryption", "Per-function IAM role, KMS encryption, no network exposure"],
         ["Denial of service", "Flood during an exam", "WAF rules; static fleet limits headroom", "WAF, throttling, reserved concurrency, budget alarms"],
         ["Elevation of privilege", "Compromised host or role", "Patching, IMDSv2, no SSH (session manager)", "No host to compromise; role limited to own tables"]],
        [1600, 1900, 2800, 2714], align=["left", "left", "left", "left"], bold_first_col=True)
    add(p_body("Secrets are kept in a secrets manager and injected at runtime. Under the shared-responsibility model AWS also secures the operating system and runtime of Lambda, so Design B has the smaller patching surface but places more weight on correct IAM policies."))
    add(p_h2("4.6 Reliability, backup and disaster recovery"))
    add(p_body("The assumed recovery targets are an RPO of at most 15 minutes and an RTO of at most one hour. The main failure modes are handled as follows."))
    add(p_body("The loss of one AZ halves the capacity of Design A (the load balancer routes to the other instance) but leaves Lambda and the database running in the remaining zones. A faulty release is handled by a rolling instance refresh with health checks (A) or a canary alias with automatic rollback (B). "
               "Data corruption is covered by automated database backups (A) and point-in-time recovery for tables (B); a regional outage by redeployment from infrastructure code and a restore of the backups in a second region; "
               "and the failure of the forecast API by the scheduler’s fallback to “run now”, so deadlines are never missed."))
    add(p_body("Of the four standard disaster-recovery strategies (backup and restore, pilot light, warm standby, active-active), backup and restore with infrastructure as code is chosen: it has the lowest standing cost, and the serverless tier is simply redeployed from a template. "
               "Whether the one-hour RTO is met must be confirmed by a recovery drill; if not, a pilot-light database replica is the next step."))
    add(p_h2("4.7 Observability, carbon dashboard and delivery"))
    add(p_body("Operations and sustainability use the same telemetry. Lambda writes one report line per invocation with duration, billed duration and maximum memory used; with the configured memory these give the energy of each request through Section 6.3. "
               "On the VM side, CPU utilisation and load-balancer request counts give the energy per request. A scheduled job joins these figures with hourly grid-intensity data and writes the daily emissions and the SCI-style indicator to a dashboard. "
               "Alarms cover the 95th-percentile latency above 100 ms, an error rate above 1 %, Lambda concurrency above 80 % of the quota and the monthly budget at 80 % of the plan; the last two address the specific serverless risks of hitting a quota during an exam and of unexpectedly high bills."))
    add(p_body("Both designs are defined as code (the prototype contains an AWS SAM template for Design B), so environments are reproducible and recovery is a redeployment. The delivery pipeline runs the unit tests, builds the package, deploys to a staging stack, "
               "runs a short Locust load test against the SLO and promotes the release through a canary alias that sends 10 % of the traffic to the new version and rolls back automatically if an alarm fires. For Design A the equivalent is an image build and a rolling instance refresh."))

    # ============================================================ 5 Technology selection
    add(p_h1("Cloud Models and Technology Selection"))
    add(p_body("@@T:t_tech@@ summarises the models and technologies chosen. A public cloud was selected because the load is highly variable and the university has no data centre of its own; a hybrid model would add an always-on on-premises tier, which is exactly the idle capacity the design tries to avoid. "
               "The same Python code runs in both designs, so any difference in the results comes from the deployment model and not from the application."))
    tab("t_tech", "Cloud models and technology choices of the two designs.",
        ["Aspect", "Design A (traditional)", "Design B (serverless, carbon-aware)"],
        [["Service model", "IaaS (EC2) plus managed load balancer and database", "FaaS (Lambda) plus managed API gateway and database"],
         ["Deployment model", "Public cloud, Tokyo region, two availability zones", "Public cloud, Tokyo region; batch jobs may run in a greener region"],
         ["Compute", "2 × t3.medium (2 vCPU, 4 GiB), gunicorn", "Lambda arm64, 256 MB, Python 3.12"],
         ["Scaling", "Static fleet sized for peak (at least 2); instances added when peak CPU exceeds 60 %", "Automatic, per request, down to zero"],
         ["Fault tolerance", "Health checks, two zones, multi-AZ database", "Provider-managed multi-AZ execution, retries, replicated database"],
         ["Operations", "Customer patches OS and runtime and manages scaling", "Provider patches OS and runtime; customer manages code and IAM"],
         ["Cost model", "Per instance-hour and per load-balancer hour (fixed)", "Per request and per GB-second (variable)"],
         ["Batch jobs", "Same fleet or a separate worker pool", "Carbon-aware scheduler, Fargate or Spot workers"]],
        [1700, 3657, 3657], align=["left", "left", "left"], bold_first_col=True)
    add(p_h2("5.1 Alternatives considered"))
    add(p_body("Besides the two simulated designs, two further compute options were considered: containers on AWS Fargate, which remove server management but still bill for running tasks, and Kubernetes on EKS, which maximises portability but adds a control plane and nodes that run continuously. "
               "A weighted decision matrix (@@T:t_matrix@@) compares the four options. The weights and scores are the author’s judgement for a campus-scale platform and are shown to make the reasoning transparent, not as measurements; "
               "Fargate and EKS were not simulated, so their cost and carbon scores are qualitative."))
    crit = [("Cost at campus scale", 0.25, [2, 3, 5, 1]), ("Carbon at campus scale", 0.25, [2, 3, 5, 1]), ("Operational effort", 0.15, [2, 4, 5, 1]),
            ("Warm and tail latency", 0.15, [5, 4, 3, 4]), ("Burst scalability", 0.10, [2, 3, 5, 3]), ("Portability, low lock-in", 0.10, [5, 4, 2, 5])]
    tot = [sum(w * sc[i] for _, w, sc in crit) for i in range(4)]
    rows = [[n, f"{int(w * 100)} %"] + [str(x) for x in sc] for n, w, sc in crit] + [["Weighted score (1–5)", "100 %"] + [f"{t:.2f}" for t in tot]]
    tab("t_matrix", "Decision matrix (scores 1 = poor, 5 = very good; author’s judgement).",
        ["Criterion", "Weight", "VMs on EC2 (A)", "Fargate", "Lambda (B)", "EKS"],
        rows, [2800, 900, 1500, 1200, 1300, 1314], align=["left", "center", "center", "center", "center", "center"], bold_first_col=False)
    add(p_body("Lambda scores highest (4.40), followed by Fargate (3.40), EC2 (2.75) and EKS (2.05). The ranking is driven by the cost, carbon and operations criteria and reverses only if portability and latency receive much more weight than sustainability. "
               "Fargate remains a sensible option for the CPU-heavy batch tier, which exceeds Lambda’s 15-minute limit."))
    # ============================================================ 6 Prototype and method
    add(p_h1("Prototype and Evaluation Method"))
    add(p_h2("6.1 Implementation"))
    add(p_body("The prototype is written in Python. *core.py* (49 lines) holds the application logic shared by both designs (login with PBKDF2, course listing, quiz and batch grading); *lambda_api.py* and *vm_app.py* are the two entry points. "
               "*carbon_model.py* (74 lines), *grid.py* (47) and *scheduler.py* (32) contain the cost–energy–carbon model, the hourly carbon-intensity series and the scheduler; they are independent of AWS and testable without credentials, whereas *scheduler_lambda.py* (44) is the thin AWS wrapper. "
               "The simulation scripts (about 620 lines), a Locust load test, an AWS SAM template and ten unit tests complete the prototype. The function that carries most of the model is the Lambda duration and cost calculation, reproduced from the source:"))
    add(p_code(excerpt("carbon_model.py", r"def lambda_duration_s", r"def lambda_cost_usd") + [""] + excerpt("carbon_model.py", r"def lambda_cost_usd", r"def lambda_energy_wh")))
    add(p_h2("6.2 Testing and validation"))
    add(p_body("Ten unit tests check the model against independent references and the scheduler against its specification, and all pass: a published Lambda worked example is reproduced (512 MB, 200 ms, 50 million requests per month give USD 86.47 after the free tier [[lambdaex]]); "
               "the Arm GB-second price is 80 % of the x86 price; CPU-bound duration halves when memory doubles up to 1,769 MB; an idle t3.medium draws (2 × 0.74 + 4 × 0.392) W × 1.135 = 3.46 W; the scheduler picks the lowest-intensity window inside the deadline "
               "and, over 200 random cases, never starts later than now + deadline − duration; and the grid series is reproducible. The tests also protect the results, because a change to a price or coefficient that breaks a published example fails immediately."))
    add(p_body("Two further checks were made. First, the closed-form calculation used in the sensitivity analysis reproduces the simulation: for the campus normal day both give a cost ratio B/A of 0.147 and an emissions ratio of 0.0091. "
               "Second, an error found during testing is instructive: a blog post cited a worked Lambda example (USD 4.67 for 1 million requests of 256 MB and 500 ms) that does not follow from the published price list, whose arithmetic gives about USD 2.28; "
               "the test therefore uses a verified example instead. The model has not been validated against measurements on AWS, which is the main open step."))
    add(p_h2("6.3 Cost, energy and carbon model"))
    add(p_body("Energy follows the CCF method [[ccf]]. With utilisation *u*, the power per vCPU is"))
    add(p_equation("*P*(*u*) = *P*_{min} + *u* (*P*_{max} − *P*_{min}),", 1))
    add(p_body("and the energy of a resource with *n*_{v} vCPUs and *m* GB of memory used for *t* hours is", cont=True))
    add(p_equation("*E* = (*n*_{v} · *P*(*u*) + *m* · *P*_{mem}) · *t* · PUE.", 2))
    add(p_body("The emissions in grams of CO_{2}e follow from the energy *E* in Wh and the grid intensity *I* in g/kWh of the region and hour:"))
    add(p_equation("*C* = *E* / 1000 × *I*.", 3))
    add(p_body("For Lambda, the warm duration of a request with CPU work *c* (seconds at one vCPU) and I/O wait *w* at memory *M* (MB) is"))
    add(p_equation("*t*_{λ} = *c* / min(*M*/1769, 1) + *w*,", 4))
    add(p_body("the billed cost per request is"))
    add(p_equation("cost = *r* + ⌈*t*_{λ}⌉_{ms} · (*M*/1024) · *p*_{arch} (+ gateway fee),", 5))
    add(p_body("where *r* is the request price and *p*_{arch} the GB-second price. The energy uses Equation (2) with *n*_{v} = *M*/1769 and *u* = 50 %, multiplied by an idle-overhead factor (1.0 in the baseline). For Design A, *u* is the simulated hourly CPU utilisation of the fleet, so idle hours are charged at idle power. "
               "Design A’s cost is the instance-hours plus the load balancer; Design B’s cost includes the API gateway fee. The free tier is not applied, so that the comparison remains valid at scale."))
    add(p_h2("6.4 Workload, simulation and parameters"))
    add(p_body("Requests arrive as a Poisson process following the daily profile of Section 3.2. The mix is 20 % login, 55 % course listing and 25 % quiz submission on normal days, and 15 %, 25 % and 60 % on exam days. "
               "The CPU time of each endpoint was measured by running the real code on the development machine (one vCPU, Xeon 2.1 GHz, Python 3.12): 5.90 ms for login, 0.018 ms for course listing and 0.52 ms for quiz grading. "
               "Design A is simulated as a queue with one server per vCPU (two instances give four servers). Design B is simulated as a pool of warm execution environments with a 15-minute keep-alive; a request that finds no idle environment pays a 300 ms cold start, which is billed. "
               "@@T:t_param@@ lists all parameters and whether each is measured, published or assumed; everything marked “assumed” should be replaced by measurements in a real deployment, and Section 7.6 shows how much each one matters. "
               "The hourly grid-intensity shapes are synthetic (a midday solar dip and an evening ramp on a regional base level), with levels of 461, 375, 315 and 25 g/kWh for Tokyo, Virginia, Oregon and Stockholm."))
    tab("t_param", "Model parameters, values and their status.",
        ["Parameter", "Value", "Source / status"],
        [["CPU time per call (login / courses / quiz)", "5.90 / 0.018 / 0.52 ms", "Measured on the prototype code"],
         ["Runtime and proxy overhead per request", "3 ms CPU", "Assumed"],
         ["Database I/O wait (login / courses / quiz)", "12 / 8 / 15 ms", "Assumed"],
         ["Lambda price", "USD 0.20 per 1M requests; 1.66667×10^{-5} (x86) and 1.33334×10^{-5} (arm) per GB-s", "Published [[lambdaprice,lambdaex]]"],
         ["API gateway price", "USD 1.00 per 1M requests", "Assumed (verify)"],
         ["EC2 t3.medium; load balancer", "USD 0.0416/h; USD 0.0225/h + 0.008 per LCU-h (1 LCU)", "Published [[ec2,alb]]"],
         ["Baseline variants (Exp. 7)", "t3.medium reserved USD 0.029/h; t4g.medium USD 0.0336/h, reserved 0.0196/h", "Published (third-party price lists) [[t3price,t4gprice]]"],
         ["Power model", "0.74–3.5 W per vCPU, 0.392 W per GB, PUE 1.135, u = 50 % for Lambda", "Published [[ccf]]"],
         ["Cold start; keep-alive", "300 ms; 15 min", "Assumed"],
         ["Grid intensity, daily mean (Tokyo / Virginia / Oregon / Stockholm)", "461 / 375 / 315 / 25 g/kWh; synthetic hourly shape", "Assumed (rounded, illustrative)"],
         ["Batch jobs", "Grading 8 vCPU × 2 h; transcoding 8 vCPU × 8 h", "Assumed"],
         ["Data moved if a job runs abroad; network energy", "1 GB (grading), 20 GB (transcoding); 0.001 kWh/GB", "Assumed; coefficient from [[ccf]]"]],
        [3100, 3600, 2314], align=["left", "left", "left"])
