# -*- coding: utf-8 -*-
"""Report text. Citations are written as [[key,key]] and numbered by first appearance."""
from docx_lib import *
import docx_lib as L

L.REFS.update({
 "masanet": "E. Masanet, A. Shehabi, N. Lei, S. Smith, J. Koomey, Recalibrating global data center energy-use estimates, Science 367 (6481) (2020) 984–986.",
 "barroso": "L.A. Barroso, U. Hölzle, The case for energy-proportional computing, IEEE Computer 40 (12) (2007) 33–37.",
 "ccf": "Cloud Carbon Footprint, Methodology (compute, memory, networking and PUE coefficients), https://www.cloudcarbonfootprint.org/docs/methodology/.",
 "sci": "Reconciling Bottom-Up Metrics with Top-Down Reporting for Cloud Carbon Accounting, arXiv:2610.10148, 2026 (survey of cloud carbon accounting and the SCI specification, ISO/IEC 21031).",
 "nist": "P. Mell, T. Grance, The NIST Definition of Cloud Computing, NIST Special Publication 800-145, 2011.",
 "jonas": "E. Jonas et al., Cloud Programming Simplified: A Berkeley View on Serverless Computing, arXiv:1902.03383, 2019.",
 "lambdaprice": "Amazon Web Services, AWS Lambda pricing, https://aws.amazon.com/lambda/pricing/.",
 "lambdaex": "D. Volkov, Amazon Lambda Pricing: Cost Breakdown for 2026, Activepieces, 22 October 2026, https://www.activepieces.com/blog/amazon-lambda-pricing-cost-breakdown-for-2026.",
 "graviton": "Amazon Web Services, AWS Lambda functions powered by AWS Graviton2 processor: run your functions on Arm and get up to 34% better price performance, AWS News Blog, https://aws.amazon.com/blogs/aws/aws-lambda-functions-powered-by-aws-graviton2-processor-run-your-functions-on-arm-and-get-up-to-34-better-price-performance/.",
 "lambdalimits": "Amazon Web Services, Lambda quotas (function memory and CPU allocation), AWS Lambda Developer Guide, https://docs.aws.amazon.com/lambda/latest/dg/limits.html.",
 "ec2": "Amazon Web Services, Amazon EC2 T3 instances (on-demand pricing), https://aws.amazon.com/ec2/instance-types/t3/.",
 "alb": "Amazon Web Services, Elastic Load Balancing pricing (Application Load Balancer hourly and LCU charges), https://aws.amazon.com/elasticloadbalancing/classicloadbalancer/pricing.",
 "pue": "Amazon Web Services, Power Usage Effectiveness (PUE) Methodology, Amazon Sustainability, December 2024, https://sustainability.aboutamazon.com/pue-methodology.pdf.",
 "ccft": "M. O’Toole, A. Bateman, M. Fraga, P. Csatlos, Updated Carbon Methodology for the AWS Customer Carbon Footprint Tool, AWS Cloud Financial Management Blog, https://aws.amazon.com/blogs/aws-cloud-financial-management/updated-carbon-methodology-for-the-aws-customer-carbon-footprint-tool.",
 "wiesner": "P. Wiesner, I. Behnke, D. Scheinert, K. Gontarska, L. Thamsen, Let’s Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud, Proc. 22nd Int. Middleware Conf. (Middleware ’21), ACM, 2021, doi:10.1145/3464298.3493399.",
})

TITLE = ["Carbon-Aware Cloud Architecture for an", "Online Education Platform: Serverless", "vs. VM Design, Prototype and Evaluation"]

ABSTRACT = ("Cloud architectures are usually judged on cost, availability and performance, while the carbon emissions they cause stay invisible. "
 "This report treats carbon as a first-class design requirement for an online education platform (login, course catalogue, quizzes, nightly grading and lecture-video transcoding). "
 "Two architectures are designed and compared: Design A, a traditional deployment on two always-on EC2 instances behind a load balancer, and Design B, a serverless deployment on AWS Lambda (arm64) "
 "with a carbon-aware scheduler for delay-tolerant batch jobs. A Python prototype was implemented, consisting of shared application code, a Lambda handler, a WSGI application, "
 "a cost–energy–carbon model based on the Cloud Carbon Footprint methodology and public AWS prices, and a scheduler that decides when and where batch jobs run. "
 "The CPU cost of each endpoint was measured, and both designs were evaluated by discrete-event simulation for a 10,000-student campus and a 60,000-student exam-day scenario. "
 "For the campus, Design B reduces daily cost by 85 % and estimated emissions by 99 % while meeting a 100 ms latency target; the cost advantage disappears above about 2.4 million requests per day, "
 "whereas the carbon advantage persists to much higher volumes unless provider-side idle overhead is large. Shifting nightly jobs in time saves 4–17 % of emissions, and moving them to a low-carbon region saves 88–94 %, "
 "but only where data-protection rules allow it. Energy is estimated rather than measured and the grid profiles are synthetic, so AWS validation with real intensity data remains future work.")
KEYWORDS = "cloud architecture design; serverless computing; AWS Lambda; carbon-aware scheduling; green cloud; energy estimation"


def build(img_info):
    """img_info: dict name -> (rid, idx, cx, cy). Returns list of XML strings for the body."""
    B = []; add = B.append
    fig_n = [0]; tab_n = [0]
    def fig(key, caption):
        fig_n[0] += 1; rid, idx, cx, cy = img_info[key]
        add(p_figure(rid, idx, cx, cy, key)); add(p_fig_caption(f"Fig.{fig_n[0]}.", caption))
        return fig_n[0]
    def tab(caption, headers, rows, widths, align=None, sz=18, bold_first_col=False):
        tab_n[0] += 1
        add(p_table_caption(f"Table {tab_n[0]}.", caption)); add(table(headers, rows, widths, align, sz, bold_first_col)); add(spacer(80))

    # ------------------------------------------------------------------ 1
    add(p_h1("Introduction"))
    add(p_body("Data centres have become one of the fastest-growing electricity consumers of the digital economy. Global estimates show that efficiency gains held the growth of data-centre energy use far below the growth of computation during the 2010s, "
               "but also that such gains cannot continue indefinitely [[masanet]]. A key reason for waste is that servers are not energy-proportional: an idle server still draws a large fraction of its peak power [[barroso]]. "
               "In the coefficients used by the Cloud Carbon Footprint (CCF) project, an average AWS vCPU draws 0.74 W when idle and 3.5 W when fully used, so an idle vCPU already costs about 21 % of a busy one [[ccf]]. "
               "For a cloud customer this means that capacity provisioned for the daily peak and left idle for the rest of the day produces emissions without producing any service."))
    add(p_body("Cloud providers rarely disclose energy or carbon data per tenant or per workload, and most accounting tools therefore rely on models and published coefficients [[ccf,sci]]. "
               "Architects who want to design for sustainability must therefore combine a model with a clear statement of its assumptions. This report takes up Topic 5 of the course (cloud architecture design for a real-world application) "
               "and adds one requirement that is usually missing from such designs: a measurable carbon target."))
    add(p_body("The application is an online education platform for a university. Three research questions guide the work. **RQ1:** can a serverless architecture meet the same latency and availability requirements as an always-on VM architecture at lower cost and lower emissions, and for which traffic volumes? "
               "**RQ2:** which configuration choices (memory size, CPU architecture, region) matter most? **RQ3:** how much can carbon-aware scheduling of delay-tolerant jobs save, and what limits it?"))
    add(p_body("The contributions are (i) a requirements analysis and two architecture designs; (ii) a working prototype with shared application code, a Lambda handler, a VM application, a carbon-aware scheduler and ten unit tests; "
               "(iii) a cost, energy and carbon model with every assumption listed and labelled as measured, published or assumed; and (iv) five experiments covering memory configuration, design comparison, region choice, scheduling and a break-even analysis. "
               "An important caveat is stated here and repeated in Section 8: the evaluation is a simulation driven by measured CPU times and published prices, not a measurement on a live AWS account. "
               "The deployment files needed to repeat it on AWS are part of the prototype."))

    # ------------------------------------------------------------------ 2
    add(p_h1("Background and Related Work"))
    add(p_h2("2.1 Service models, deployment models and serverless computing"))
    add(p_body("The NIST definition distinguishes the service models IaaS, PaaS and SaaS and the deployment models private, community, public and hybrid cloud [[nist]]. "
               "Amazon EC2 is IaaS: the customer rents virtual machines and remains responsible for the operating system, runtime, patching and scaling. "
               "AWS Lambda is a function-as-a-service platform, the core of serverless computing, in which the provider runs the servers, scales the number of execution environments with demand, and bills for use rather than for reserved capacity [[jonas]]."))
    add(p_body("Lambda bills two items: a request charge of USD 0.20 per million requests and a duration charge per GB-second of configured memory, USD 0.0000166667 on x86 and USD 0.0000133334 on Arm (Graviton), "
               "with duration rounded up to 1 ms [[lambdaprice,lambdaex]]. The Arm price is about 20 % lower and AWS reports up to 34 % better price-performance [[graviton]]. "
               "CPU power is allocated in proportion to configured memory, and a function with 1,769 MB has the equivalent of one vCPU [[lambdalimits]]. Memory therefore controls both price and speed, which is exploited in Experiment 1."))
    add(p_h2("2.2 Estimating energy and carbon in the cloud"))
    add(p_body("The CCF method, which builds on Etsy’s Cloud Jewels, estimates average power per vCPU from utilisation *u* as *P* = *P*_{min} + *u*(*P*_{max} − *P*_{min}), multiplies it by vCPU-hours, and adds terms for memory and networking [[ccf]]. "
               "The result is multiplied by the provider’s power usage effectiveness (PUE), 1.135 for AWS in CCF, and by the grid emission factor of the region [[ccf]]. AWS publishes its own PUE methodology [[pue]]. "
               "When utilisation is unknown, CCF falls back to 50 %. Estimates of this kind are location-based; AWS’s Customer Carbon Footprint Tool additionally reports market-based figures and allocates the emissions of unused capacity proportionally to customers [[ccft]]. "
               "That allocation is relevant for serverless: a function that runs for 40 ms is not charged for idle servers by the simple model above, but a provider-level view does attribute some idle overhead to it. Section 7.5 tests how sensitive the conclusions are to this overhead. "
               "The Software Carbon Intensity (SCI) specification, standardised as ISO/IEC 21031, expresses emissions per functional unit of work [[sci]]; the metric “gCO_{2}e per 1,000 requests” used here is an SCI-style indicator restricted to operational emissions."))
    add(p_h2("2.3 Carbon-aware computing"))
    add(p_body("The carbon intensity of the public grid fluctuates over the day with demand and with the share of variable renewables. Carbon-aware computing exploits this by running flexible work when, or where, electricity is cleaner. "
               "Wiesner et al. analysed temporal shifting of delay-tolerant workloads for Germany, Great Britain, France and California and found that the potential depends strongly on the regional energy mix, the time constraints of the job and the accuracy of intensity forecasts [[wiesner]]. "
               "Grids with much wind and solar offer large potential, whereas a largely nuclear grid such as France’s varies little [[wiesner]]. These three factors (window, forecast error, grid variability) reappear as the sweep parameters of Experiment 4."))

    # ------------------------------------------------------------------ 3
    add(p_h1("Scenario and Requirements"))
    add(p_body("The platform serves the students of one university, located in UTC+8, from the AWS Tokyo region (ap-northeast-1). Students log in, browse the course catalogue and submit quizzes that combine ten multiple-choice questions with a short free-text answer. "
               "Two delay-tolerant jobs run behind the scenes: a nightly job that re-grades all submissions and builds reports, and the transcoding of newly uploaded lecture videos. "
               "Table 1 lists the functional and non-functional requirements. Quantities that were not given by a real operator are assumptions and are marked as such."))
    tab("Functional (F) and non-functional (N) requirements of the platform.",
        ["ID", "Requirement", "Target / assumption"],
        [["F1", "Login", "Password verification and token issue"],
         ["F2", "Course catalogue", "Paged list of about 60 courses"],
         ["F3", "Quiz submission", "10 multiple-choice answers plus a free-text answer, graded on submit"],
         ["F4", "Nightly grading and reports", "All submissions re-graded; results ready by 08:00 (job ready 23:00, deadline 9 h)"],
         ["F5", "Lecture-video transcoding", "Ready at 18:00, to be finished within 24 h"],
         ["N1", "Load", "Campus: 10,000 active students × 30 requests = 300,000 requests/day. Large: 60,000 students. Exam day: 3× the volume, with the 14:00–16:00 hours weighted 5× (assumed)"],
         ["N2", "Latency", "Warm-path latency of every API call ≤ 100 ms"],
         ["N3", "Availability", "99.9 % per month (about 43 min of downtime), no single point of failure"],
         ["N4", "Storage", "About 5 TB of lecture video and 200 GB of database (assumed; identical in both designs)"],
         ["N5", "Security", "TLS everywhere, least-privilege IAM, encryption at rest, personal data kept in the home region"],
         ["N6", "Budget", "At most USD 100 per month for compute at campus scale (assumed)"],
         ["N7", "Carbon", "Report gCO_{2}e per day and per 1,000 requests; minimise subject to N2 and N3"]],
        [700, 2300, 6014], align=["left", "left", "left"])

    # ------------------------------------------------------------------ 4
    add(p_h1("Cloud Architecture Design"))
    add(p_body("Two architectures were designed for the same requirements. Both serve the static front-end from S3 behind CloudFront and both use a managed database, so these shared components are excluded from the comparison. "
               "They differ in how the dynamic API is executed and in how batch work is handled (Fig. 1)."))
    fig("fig_architecture", "The two compared architectures. Design A runs the API on two always-on EC2 instances in different availability zones behind an Application Load Balancer; Design B runs it on AWS Lambda (arm64, 256 MB) behind an API gateway.")
    add(p_h2("4.1 Design A: always-on virtual machines"))
    add(p_body("Design A places an Application Load Balancer in front of two t3.medium instances (2 vCPU, 4 GiB) in two availability zones. Each instance runs the application with gunicorn. The fleet is static and sized so that the peak CPU demand stays below 60 % utilisation, with a minimum of two instances for availability: "
               "*n* = max(2, ⌈peak vCPU demand / (0.6 × 2)⌉). Availability comes from the load balancer’s health checks and the two zones; the customer operates the operating system, the runtime and the scaling rules. "
               "The cost is nearly fixed, because instances and the load balancer are billed per hour whether or not requests arrive."))
    add(p_h2("4.2 Design B: serverless with a carbon-aware batch pipeline"))
    add(p_body("Design B runs the same application code as an AWS Lambda function on arm64 with 256 MB of memory, behind an API gateway, with an on-demand database. Execution environments are created per request and removed after a period of inactivity, so the platform scales down to almost nothing at night and up on exam days without any scaling rules; in the simulation the pool of warm environments peaked at 6 on a normal campus day, 13 on the campus exam day and 38 on the large exam day. "
               "The memory setting was chosen by the sweep in Experiment 1: 256 MB is the smallest value for which the slowest endpoint (login) stays below the 100 ms target (128 MB would need about 135 ms)."))
    add(p_body("Delay-tolerant jobs are handled by the carbon-aware pipeline in Fig. 2. When a job becomes ready, EventBridge invokes a scheduler function with the job’s duration and deadline. The function obtains an hourly carbon-intensity forecast, "
               "selects the start hour inside the window [now, now + deadline − duration] that minimises the mean forecast intensity over the run (ties go to the earliest hour), and creates a one-time schedule for that hour. "
               "In the spatio-temporal variant the same search runs over several regions, with a penalty for the carbon of moving data, and only regions that are allowed for the job’s data are considered. "
               "If the forecast service is unreachable the function falls back to “run now”, so that the deadline is never endangered; a unit test confirms that the chosen start never exceeds the deadline."))
    fig("fig_pipeline", "Carbon-aware batch pipeline. A scheduler function chooses the start hour (and, for anonymised data, the region) before the batch workers run.")

    # ------------------------------------------------------------------ 5
    add(p_h1("Cloud Models and Technology Selection"))
    add(p_body("Table 2 summarises the models and technologies chosen. A public cloud was selected because the load is highly variable and the university has no data centre of its own; a hybrid model would add an always-on on-premises tier, which is exactly the idle capacity the design tries to avoid. "
               "The same Python code runs in both designs, so any difference in the results comes from the deployment model and not from the application."))
    tab("Cloud models and technology choices of the two designs.",
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
    add(p_body("Arm64 was chosen for Lambda because the price per GB-second is about 20 % lower for unchanged Python code [[lambdaprice,graviton]]. For security, both designs terminate TLS at the edge or load balancer, use least-privilege IAM roles, encrypt data at rest and keep personal data in the home region. "
               "Under the shared-responsibility model, Design B shifts operating-system and runtime patching to the provider, whereas Design A leaves it with the university."))

    # ------------------------------------------------------------------ 6
    add(p_h1("Prototype and Evaluation Method"))
    add(p_h2("6.1 Prototype"))
    add(p_body("The prototype is written in Python and organised as follows: *core.py* (login with PBKDF2, course listing, quiz grading and batch grading), *lambda_api.py* (Design B handler), *vm_app.py* (Design A WSGI application), "
               "*carbon_model.py* (cost, energy and carbon functions), *grid.py* (hourly carbon-intensity series), *scheduler.py* (temporal and spatio-temporal selection), *scheduler_lambda.py* (AWS deployment of the scheduler), "
               "a Locust load test, an AWS SAM template and the simulation scripts. Ten unit tests pass. They include a check that the Lambda cost function reproduces a published worked example (512 MB, 200 ms, 50 million requests per month: USD 86.47 after the free tier [[lambdaex]]) "
               "and a randomised check that the scheduler never starts a job later than its deadline allows."))
    add(p_h2("6.2 Cost, energy and carbon model"))
    add(p_body("Energy follows the CCF method [[ccf]]. With utilisation *u*, the power per vCPU is"))
    add(p_equation("*P*(*u*) = *P*_{min} + *u* (*P*_{max} − *P*_{min}),", 1))
    add(p_body("and the energy of a resource with *n*_{v} vCPUs and *m* GB of memory used for *t* hours is", cont=True))
    add(p_equation("*E* = (*n*_{v} · *P*(*u*) + *m* · *P*_{mem}) · *t* · PUE.", 2))
    add(p_body("The emissions in grams of CO_{2}e follow from the energy *E* in Wh and the grid intensity *I* in g/kWh of the region and hour:"))
    add(p_equation("*C* = *E* / 1000 × *I*.", 3))
    add(p_body("For Lambda, the warm duration of a request with CPU work *c* (seconds at one vCPU) and I/O wait *w* at memory *M* (MB) is"))
    add(p_equation("*t*_{λ} = *c* / min(*M*/1769, 1) + *w*,", 4))
    add(p_body("the billed cost is *r* + ⌈*t*_{λ}⌉_{ms} · (*M*/1024) · *p*_{arch}, and the energy uses Equation (2) with *n*_{v} = *M*/1769 and *u* = 50 %. For Design A, *u* is the simulated hourly CPU utilisation of the fleet, so idle hours are charged at idle power. "
               "Design A’s cost is the instance-hours plus the load balancer; Design B’s cost includes the API gateway fee. The free tier is not applied, so that the comparison remains valid at scale.", cont=True))
    add(p_h2("6.3 Workload, simulation and what is measured"))
    add(p_body("Requests arrive as a Poisson process following a daily profile with peaks in the morning, afternoon and evening. The mix is 20 % login, 55 % course listing and 25 % quiz submission on normal days, and 15 %, 25 % and 60 % on exam days. "
               "The CPU time of each endpoint was measured by running the real code on the development machine (one vCPU, Xeon 2.1 GHz, Python 3.12): 5.90 ms for login, 0.018 ms for course listing and 0.52 ms for quiz grading. "
               "Design A is simulated as a queue with four CPU servers (two instances with two vCPUs). Design B is simulated as a pool of warm execution environments with a 15-minute keep-alive; a request that finds no idle environment pays a 300 ms cold start, which is billed. "
               "Table 3 lists all parameters and whether each is measured, published or assumed. Everything marked “assumed” is a modelling choice that should be replaced with measurements in a real deployment."))
    tab("Model parameters, values and their status.",
        ["Parameter", "Value", "Source / status"],
        [["CPU time per call (login / courses / quiz)", "5.90 / 0.018 / 0.52 ms", "Measured on the prototype code"],
         ["Runtime and proxy overhead per request", "3 ms CPU", "Assumed"],
         ["Database I/O wait (login / courses / quiz)", "12 / 8 / 15 ms", "Assumed"],
         ["Lambda price", "USD 0.20 per 1M requests; 1.66667×10^{-5} (x86) and 1.33334×10^{-5} (arm) per GB-s", "Published [[lambdaprice,lambdaex]]"],
         ["API gateway price", "USD 1.00 per 1M requests", "Assumed (verify)"],
         ["EC2 t3.medium; load balancer", "USD 0.0416/h; USD 0.0225/h + 0.008 per LCU-h (1 LCU)", "Published [[ec2,alb]]"],
         ["Power model", "0.74–3.5 W per vCPU, 0.392 W per GB, PUE 1.135, u = 50 % for Lambda", "Published [[ccf]]"],
         ["Cold start; keep-alive", "300 ms; 15 min", "Assumed"],
         ["Grid intensity, daily mean (Tokyo / Virginia / Oregon / Stockholm)", "461 / 375 / 315 / 25 g/kWh; synthetic hourly shape", "Assumed (rounded, illustrative)"],
         ["Batch jobs", "Grading 8 vCPU × 2 h; transcoding 8 vCPU × 8 h", "Assumed"],
         ["Data moved if a job runs abroad; network energy", "1 GB (grading), 20 GB (transcoding); 0.001 kWh/GB", "Assumed; coefficient from [[ccf]]"]],
        [3100, 3600, 2314], align=["left", "left", "left"])

    # ------------------------------------------------------------------ 7
    add(p_h1("Results and Evaluation"))
    add(p_h2("7.1 Experiment 1: memory size and CPU architecture"))
    add(p_body("Memory size was swept from 128 MB to 3,008 MB for two workloads on x86 and arm64: the I/O-dominated API mix (about 4.3 ms of CPU and 10.6 ms of I/O wait per request) and a CPU-dominated batch grading call (1.5 s of CPU). "
               "Table 4 and Fig. 3 show opposite behaviour. For the API, a larger memory buys little: the duration falls from 40.4 ms at 256 MB to 14.9 ms at 1,769 MB, but the cost per million requests rises from USD 0.337 to 0.546 (+62 %), "
               "because the fixed I/O wait is billed at a higher memory price. For the CPU-dominated call, cost and energy stay almost flat from 256 MB to 1,769 MB (USD 34.9–35.9 per million) while the duration falls from 10.4 s to 1.55 s, "
               "so the extra speed is almost free. Above 1,769 MB the duration no longer improves, because the single-threaded code cannot use a second vCPU, but the cost rises by 70 % (USD 60.9 per million at 3,008 MB) and the energy from 1.37 to 2.32 Wh per thousand calls. "
               "Arm64 lowered the total cost by 8.5–15.7 % for the API mix (the fixed request fee dilutes the 20 % duration discount) and by about 19.9 % for the CPU-dominated call. Energy follows cost closely because both grow with allocated memory multiplied by time."))
    tab("Memory sweep on arm64 (cost excludes the API gateway).",
        ["Workload", "Memory (MB)", "Duration (ms)", "Cost (USD per 1M req.)", "Energy (Wh per 1,000 req.)"],
        [["API mix (I/O-dominated)", "256", "40.4", "0.337", "0.005"],
         ["", "1,769", "14.9", "0.546", "0.013"],
         ["", "3,008", "14.9", "0.788", "0.022"],
         ["Batch grading (1.5 s CPU)", "256", "10,415", "34.92", "1.329"],
         ["", "1,769", "1,550", "35.90", "1.367"],
         ["", "3,008", "1,550", "60.91", "2.324"]],
        [2700, 1300, 1500, 1800, 1714], align=["left", "center", "center", "center", "center"])
    fig("fig_memory", "Memory sweep for the two workloads. Lines show cost on x86 and arm64 (left axis); the dashed line shows the duration on arm64 (right axis, logarithmic).")
    add(p_body("Two practical rules follow. I/O-bound request handlers should use the smallest memory that meets the latency target. CPU-bound functions should be raised to about 1,769 MB (one vCPU) and not further unless the code is multi-threaded."))

    add(p_h2("7.2 Experiment 2: Design A versus Design B"))
    add(p_body("Both designs were simulated for a normal campus day, a campus exam day and a large exam day. Fig. 4 shows the daily pattern for the normal day. Design A emits about 3 g CO_{2}e every hour of the day because its two instances draw their idle power "
               "regardless of traffic, whereas the emissions of Design B follow the request curve, from about 0.001 g in the early morning to about 0.06 g at the evening peak. The mean CPU utilisation of Design A is only 0.4 % on a normal day (peak 0.7 %), 1.1 % on the campus exam day (peak 6.5 %) and 6.6 % on the large exam day (peak 39 %)."))
    fig("fig_hourly", "Left: hourly requests (bars) and the assumed grid intensity of the Tokyo region (line). Right: hourly emissions of the two designs on a normal campus day (logarithmic axis).")
    add(p_body("Table 5 and Fig. 5 give the daily totals. On the normal campus day Design B costs USD 0.40 against USD 2.73 (−85 %) and emits 0.70 g against 77.1 g (−99 %). On the campus exam day the figures are USD 1.21 against 2.73 (−56 %) and 2.1 g against 78.0 g (−97 %). "
               "On the large exam day, with 5.4 million requests, Design B emits 12.8 g against 85.3 g (−85 %) but is now more expensive: USD 7.24 against 2.73 (+165 %). "
               "Both designs met the latency target in every scenario and Design A never queued, because even the large exam day needs less than 40 % of its four vCPUs at the peak. "
               "The 95th-percentile latency of Design B at 256 MB is 73.5 ms against 20.9 ms for Design A; it is dominated by the login call, which receives only 0.14 vCPU. The percentiles p95 and p99 coincide because latency is determined mainly by the type of endpoint. "
               "A variant at 1,769 MB (B-fast) matches the latency of Design A (20.9 ms) for 17 % more cost than B at 256 MB on the normal day, at 2.5 times the emissions of B at 256 MB, but still 98 % below Design A. "
               "In the model, cold starts affect at most 0.002 % of requests, because the traffic is steady; real cold-start rates depend on bursts and on how often the platform recycles environments, which the simulation does not capture."))
    tab("Daily cost, estimated energy, emissions and latency of the designs.",
        ["Scenario", "Design", "Cost (USD/day)", "Energy (Wh/day)", "CO_{2}e (g/day)", "p95 (ms)"],
        [["Campus, normal day (300k req.)", "A: 2 × t3.medium", "2.73", "167.2", "77.1", "20.9"],
         ["", "B: Lambda 256 MB", "0.40", "1.5", "0.70", "73.5"],
         ["", "B-fast: Lambda 1,769 MB", "0.47", "3.9", "1.78", "20.9"],
         ["Campus, exam day (900k req.)", "A: 2 × t3.medium", "2.73", "169.3", "78.0", "20.9"],
         ["", "B: Lambda 256 MB", "1.21", "4.8", "2.13", "73.5"],
         ["", "B-fast: Lambda 1,769 MB", "1.44", "13.5", "5.97", "20.9"],
         ["Large, exam day (5.4M req.)", "A: 2 × t3.medium", "2.73", "185.8", "85.3", "20.9"],
         ["", "B: Lambda 256 MB", "7.24", "28.8", "12.76", "73.5"],
         ["", "B-fast: Lambda 1,769 MB", "8.66", "81.0", "35.82", "20.9"]],
        [2250, 2100, 1150, 1250, 1150, 1114], align=["left", "left", "center", "center", "center", "center"])
    fig("fig_designs", "Daily cost (left) and daily emissions (right, logarithmic axis) of Design A, Design B at 256 MB and Design B at 1,769 MB in the three scenarios.")

    add(p_h2("7.3 Experiment 3: choice of region"))
    add(p_body("Running the same workload in other regions changes only the grid intensity in the model (Table 6). Relative to Tokyo, the Virginia and Oregon regions lower the emissions of Design B by 16 % and 28 %, and Stockholm by 95 %. "
               "The same percentages apply to Design A, whose absolute emissions are about a hundred times higher. Moving the interactive API abroad would, however, add network latency for students in China and may conflict with data-protection rules, "
               "so a change of region is attractive mainly for batch jobs, which are examined next."))
    tab("Daily emissions of the normal campus day by region (assumed, rounded intensities).",
        ["Region", "Mean intensity (g/kWh)", "Design A (g/day)", "Design B (g/day)", "Design B vs. Tokyo"],
        [["Tokyo (ap-northeast-1)", "461", "77.1", "0.70", "–"],
         ["N. Virginia (us-east-1)", "375", "62.7", "0.59", "−15.6 %"],
         ["Oregon (us-west-2)", "315", "52.6", "0.50", "−28.3 %"],
         ["Stockholm (eu-north-1)", "25", "4.1", "0.04", "−94.7 %"]],
        [2500, 1800, 1500, 1500, 1714], align=["left", "center", "center", "center", "center"])

    add(p_h2("7.4 Experiment 4: carbon-aware scheduling of batch jobs"))
    add(p_body("The scheduler was evaluated over 60 simulated days with day-to-day fluctuation in the grid and a forecast error of 6 %. Four strategies were compared: running immediately in Tokyo, shifting in time within the deadline window, moving to the cleanest region without waiting, and combining both (Table 7). "
               "Temporal shifting alone saves 4.4 % for the nightly grading job (9 h window, mean delay 4.5 h) and 16.5 % for the transcoding job (24 h window, mean delay 14.1 h). Moving the jobs to Stockholm saves 93.5 % and 88.2 %, and combining both adds almost nothing, "
               "because the regional difference dominates the hourly difference. The residual emissions of the regional strategy are largely caused by the data transfer: for the transcoding job, moving 20 GB accounts for about 9 g of the 17 g that remain, "
               "so transfer volume must be included in any regional decision. As the regional strategy is only permissible for data that may leave the home region, it is limited here to anonymised inputs."))
    tab("Emissions per job under four scheduling strategies (mean ± standard deviation over 60 days).",
        ["Job", "Strategy", "CO_{2}e per job (g)", "Saving (%)", "Mean delay (h)"],
        [["Nightly grading (8 vCPU × 2 h, 9 h window)", "Run immediately", "35.0 ± 2.4", "–", "0"],
         ["", "Shift in time", "33.5 ± 2.4", "4.4", "4.5"],
         ["", "Move region", "2.28 ± 0.12", "93.5", "0"],
         ["", "Time and region", "2.26 ± 0.12", "93.6", "2.7"],
         ["Video transcoding (8 vCPU × 8 h, 24 h window)", "Run immediately", "143.5 ± 8.6", "–", "0"],
         ["", "Shift in time", "119.9 ± 7.6", "16.5", "14.1"],
         ["", "Move region", "17.0 ± 0.8", "88.2", "0"],
         ["", "Time and region", "16.9 ± 0.8", "88.3", "6.3"]],
        [3000, 1800, 1700, 1250, 1264], align=["left", "left", "center", "center", "center"])
    add(p_body("Fig. 6 shows how the saving of temporal shifting depends on three factors. First, the window: nothing can be saved until the window exceeds the job duration; for the 2-hour grading job the saving is 4.4 % at 9 h, 12.4 % at 12 h and about 18–19 % at 18 h or more, "
               "while the 8-hour transcoding job needs a window of about 18 h to reach 10 % and 24 h to reach 16.5 %. Second, forecast accuracy: with a 24 h window, the saving of the grading job falls from 19.3 % with a perfect forecast to 17.0 % at 10 % error and 8.4 % at 40 % error. "
               "Third, the variability of the grid: scaling the daily swing of the synthetic profile by factors of 0, 1 and 2 changes the saving of the grading job from 6.2 % to 18.5 % and 35.5 %. The 6 % at zero swing comes from the random fluctuation in the model. "
               "These results agree in direction with the literature [[wiesner]], but their absolute size depends on the assumed profile and must be re-estimated with real intensity data."))
    fig("fig_scheduler", "Saving of temporal shifting versus run-now as a function of the flexibility window (left), the forecast error (centre, 24 h window) and the grid variability (right, 24 h window).")

    add(p_h2("7.5 Experiment 5: break-even analysis"))
    add(p_body("To find out whether the advantage of Design B is a feature of small platforms, the daily request volume was varied from 10^{4} to 10^{9}. Design A is resized to the peak at each volume (at least two instances). Fig. 7 shows the result. "
               "In cost, the lines cross at about 2.4 million requests per day (an average of 27 requests per second). At 10^{8} requests per day Design A needs 8 instances (USD 8.72 per day) against USD 134 for Design B, and at 10^{9} requests it needs 80 instances (USD 80.6) against USD 1,340. "
               "The API gateway fee, assumed at USD 1.00 per million requests, makes up 75 % of the per-request cost of Design B; without it, the crossover would move to roughly 8 million requests per day."))
    add(p_body("In emissions, Design B stays below Design A over the entire range if the provider-side idle overhead is ignored (factor 1.0) or set to 1.5. If the overhead is set to 2.0, that is, if the provider attributes twice the modelled energy to each Lambda request, the lines cross at about 75 million requests per day. "
               "The carbon advantage of serverless therefore rests on avoiding idle capacity: it is robust for small and medium platforms and weakens only at a scale where a VM fleet would run at high utilisation. "
               "Because the true overhead is not observable by the customer, this factor is the largest source of uncertainty in the comparison."))
    fig("fig_breakeven", "Break-even analysis. Left: cost per day versus requests per day. Right: emissions per day for Design A and for Design B under idle overhead factors of 1.0, 1.5 and 2.0 (dotted line: crossover for factor 2.0).")

    # ------------------------------------------------------------------ 8
    add(p_h1("Discussion"))
    add(p_h2("8.1 Evaluation against the requirements"))
    add(p_body("Table 8 summarises how the designs fare against the evaluation criteria of the assignment. Both meet the latency and availability targets in the simulation. The difference lies in cost structure and emissions: Design A pays for idle capacity, Design B pays per use."))
    tab("Evaluation of the two designs.",
        ["Criterion", "Design A (VMs)", "Design B (serverless)"],
        [["Scalability", "Manual or rule-based; static fleet handled the large exam day at 39 % peak utilisation", "Automatic; no scaling rules; limited only by account concurrency quotas"],
         ["Availability", "Two zones and health checks; failover depends on correct configuration", "Multi-AZ by default; fewer components to operate"],
         ["Performance", "p95 20.9 ms", "p95 73.5 ms at 256 MB; 20.9 ms at 1,769 MB; cold starts not captured"],
         ["Security", "More surface to patch (OS, runtime, SSH, AMIs)", "Smaller surface; IAM policy per function becomes the main control"],
         ["Cost", "USD 2.73/day at any campus volume; cheaper above about 2.4M requests/day", "USD 0.40–7.24/day in the scenarios; cheaper below about 2.4M requests/day"],
         ["Carbon", "77–85 g/day, dominated by idle power", "0.7–12.8 g/day (−85 % to −99 %), sensitive to the idle overhead assumption"]],
        [1500, 3757, 3757], align=["left", "left", "left"], bold_first_col=True)
    add(p_h2("8.2 Limitations"))
    add(p_body("The results must be read within the following limits. (1) The experiments are simulations, driven by measured CPU times, published prices and CCF coefficients; no workload was run on an AWS account, and energy is estimated rather than metered. "
               "(2) The hourly grid profiles are synthetic and the regional levels are rounded, illustrative values, so the absolute savings of Experiments 3 and 4 are not predictions. "
               "(3) Only operational, location-based emissions are modelled; embodied emissions and market-based accounting are excluded [[ccf,ccft]]. "
               "(4) Shared components (database, object storage, CDN, data transfer) are excluded. In practice an always-on RDS instance would add idle energy to Design A. "
               "(5) Burstable-CPU credit behaviour of t3 instances is ignored, and the lower power of Graviton processors is not credited to Design B, which is conservative. "
               "(6) Cold starts and environment recycling are simplified. (7) The scheduling results come from one random seed over 60 days, and the CPU timings come from a single machine."))
    add(p_h2("8.3 Improvements and recommendations"))
    add(p_body("The next step is to deploy both designs with the supplied SAM template and load test, to replace the model inputs with CloudWatch duration and memory records and with the provider’s own carbon reports, and to feed the scheduler with real forecasts from an intensity service. "
               "A stronger baseline for Design A would use Arm instances, reserved capacity or autoscaling. For a university platform of the size studied here, the results support the following practice: serve the interactive tier on a serverless platform at the smallest memory that meets the latency target; "
               "give delay-tolerant jobs at least 12–24 hours of flexibility and schedule them by forecast; move jobs to another region only for anonymised data and after counting the transfer; and track emissions per 1,000 requests as an SCI-style indicator [[sci]]."))

    # ------------------------------------------------------------------ 9
    add(p_h1("Conclusion"))
    add(p_body("This report designed and evaluated two architectures for an online education platform and treated carbon emissions as a requirement next to cost, availability and latency. "
               "For a campus of 10,000 students, a serverless design on Lambda met a 100 ms latency target while reducing daily cost by 85 % and estimated emissions by 99 % compared with two always-on VMs, because the VMs run at under 1 % utilisation on a normal day. "
               "The cost advantage ends at roughly 2.4 million requests per day, mainly because of the API gateway fee, whereas the carbon advantage persists to far larger volumes unless the provider’s idle overhead is about twice what the model assumes. "
               "Memory configuration matters in opposite ways for I/O-bound and CPU-bound code, and Arm64 gives a steady 20 % price reduction. Carbon-aware scheduling saved 4–17 % by shifting nightly jobs in time and 88–94 % by moving them to a low-carbon region, "
               "provided the deadline window is long, the forecast is reasonable, the data may leave the region and the transfer is small. "
               "The main limitation is that energy and grid data are modelled; deploying the prototype on AWS with real carbon-intensity data is the natural continuation of this work."))
    return B


def reference_list():
    return [p_ref(L.REFS[k]) for k, _ in sorted(L.CITES.items(), key=lambda kv: kv[1])]
