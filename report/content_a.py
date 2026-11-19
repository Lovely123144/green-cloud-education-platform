# -*- coding: utf-8 -*-
from docx_lib import *

def part_a(add, fig, tab):
    # ============================================================ 1 Introduction
    add(p_h1("Introduction"))
    add(p_h2("1.1 Motivation and problem statement"))
    add(p_body("Data centres have become one of the fastest-growing electricity consumers of the digital economy. Global estimates show that efficiency gains held the growth of data-centre energy use far below the growth of computation during the 2010s, "
               "but also that such gains cannot continue indefinitely [[masanet]]. A key reason for waste is that servers are not energy-proportional: an idle server still draws a large fraction of its peak power [[barroso]]. "
               "In the coefficients used by the Cloud Carbon Footprint (CCF) project, an average AWS vCPU draws 0.74 W when idle and 3.5 W when fully used, so an idle vCPU already costs about 21 % of a busy one [[ccf]]. "
               "For a cloud customer this means that capacity provisioned for the daily peak and left idle for the rest of the day produces emissions without producing any service."))
    add(p_body("Online education makes the problem concrete, because traffic follows the timetable: almost absent at night, high around lectures and spiking when a quiz or exam starts. "
               "Cloud providers rarely disclose energy or carbon data per tenant or per workload, and most accounting tools therefore rely on models and published coefficients [[ccf,sci]]. "
               "Architects who want to design for sustainability must therefore combine a model with a clear statement of its assumptions. This report takes up Topic 5 of the course (cloud architecture design for a real-world application) "
               "and adds one requirement that is usually missing from such designs: a measurable carbon target."))
    add(p_h2("1.2 Objectives and research questions"))
    add(p_body("The objective is to design, prototype and evaluate a cloud architecture for an online education platform in which cost, availability, performance, security and carbon emissions are all treated as design requirements, and to state clearly what the evidence does and does not show. "
               "Three research questions guide the evaluation. **RQ1:** can a serverless architecture meet the same latency and availability requirements as an always-on VM architecture at lower cost and lower emissions, and for which traffic volumes? "
               "**RQ2:** which configuration choices (memory size, CPU architecture, region) and which model assumptions matter most? **RQ3:** how much can carbon-aware scheduling of delay-tolerant jobs save, and what limits it?"))
    add(p_h2("1.3 Approach, contributions and structure"))
    add(p_body("The contributions are (i) a requirements analysis, workload characterisation and two architecture designs with security, reliability, observability and delivery aspects; (ii) a working prototype with shared application code, a Lambda handler, a VM application, a carbon-aware scheduler and ten unit tests; "
               "(iii) a cost, energy and carbon model with every assumption listed and labelled as measured, published or assumed; and (iv) eight experiments covering memory configuration, design comparison, region choice, scheduling, a break-even analysis, a sensitivity analysis, stronger baselines and a flash crowd. "
               "An important caveat is stated here and repeated in Section 8: the evaluation is a simulation driven by measured CPU times and published prices, not a measurement on a live AWS account. "
               "The deployment files needed to repeat it on AWS are part of the prototype."))
    add(p_body("Section 2 reviews the background, Section 3 defines scenario and requirements, Section 4 the architecture, Section 5 the technology choices and Section 6 the prototype and method. Section 7 reports the eight experiments, Section 8 discusses them and Section 9 concludes."))

    # ============================================================ 2 Background
    add(p_h1("Background and Related Work"))
    add(p_h2("2.1 Cloud computing fundamentals and the AWS infrastructure"))
    add(p_body("The NIST definition describes cloud computing through five essential characteristics (on-demand self-service, broad network access, resource pooling, rapid elasticity and measured service), three service models (IaaS, PaaS and SaaS) "
               "and four deployment models (private, community, public and hybrid cloud) [[nist]]. Rapid elasticity and measured service are the characteristics that matter most here: they allow capacity to follow demand and charge for what is used."))
    add(p_body("AWS organises its infrastructure into Regions (isolated geographic areas) and Availability Zones (AZs, separate data-centre groups inside a Region). "
               "Spreading components over at least two AZs protects against the failure of one facility, and the choice of Region influences latency, jurisdiction, price and, as shown later, the carbon intensity of the electricity."))
    add(p_h2("2.2 Virtual machines, containers and functions"))
    add(p_body("Compute can be consumed as virtual machines, containers or functions (@@T:t_gran@@): the unit of deployment shrinks from a whole operating system to a piece of code, and billing moves from reserved capacity to actual use."))
    tab("t_gran", "Compute granularities in the cloud (qualitative comparison).",
        ["Aspect", "Virtual machine", "Container", "Function (FaaS)"],
        [["Unit of deployment", "Operating-system image", "Application plus dependencies", "Code package and handler"],
         ["Isolation", "Hypervisor, strong", "Kernel namespaces, medium", "Platform sandbox per environment"],
         ["Start-up", "Minutes", "Seconds", "Milliseconds to about a second (cold start)"],
         ["Scaling unit", "Instance", "Task or pod", "Concurrent invocation"],
         ["Billing", "Per hour or second while running", "Per vCPU and memory while running", "Per request and GB-second used"],
         ["Operator effort", "High (OS, patches, scaling)", "Medium (image, orchestration)", "Low (code and permissions)"],
         ["Typical fit", "Stable, long-running services", "Microservices, portable workloads", "Spiky, short, event-driven work"]],
        [1700, 2300, 2400, 2614], align=["left", "left", "left", "left"], bold_first_col=True)
    add(p_h2("2.3 The serverless execution model"))
    add(p_body("In AWS Lambda the first request to a function causes the platform to create an execution environment, load the code, start the runtime and run the initialisation code; this is the cold start. "
               "Later requests are served by the same environment (warm start) for as long as the platform keeps it. An environment handles one request at a time, so concurrent requests need as many environments, "
               "and a sudden burst makes many requests pay the cold-start delay at once [[jonas]]. Lambda limits a single invocation to 15 minutes and offers configurable memory up to about 10 GB [[lambdalimits]]; "
               "long-running, stateful or heavily CPU-bound work therefore needs another service, such as containers on Fargate or batch workers on EC2."))
    add(p_body("Lambda bills two items: a request charge of USD 0.20 per million requests and a duration charge per GB-second of configured memory, USD 0.0000166667 on x86 and USD 0.0000133334 on Arm (Graviton), "
               "with duration rounded up to 1 ms [[lambdaprice,lambdaex]]. The Arm price is about 20 % lower and AWS reports up to 34 % better price-performance [[graviton]]. "
               "CPU power is allocated in proportion to configured memory, and a function with 1,769 MB has the equivalent of one vCPU [[lambdalimits]]. Memory therefore controls both price and speed, which is exploited in Experiment 1."))
    add(p_h2("2.4 Energy use and carbon accounting"))
    add(p_body("Three notions are needed. The **power usage effectiveness (PUE)** is the ratio of the total energy of a facility to the energy used by its IT equipment; AWS publishes its PUE methodology [[pue]] and CCF uses 1.135 for AWS [[ccf]]. "
               "The **grid emission factor** or carbon intensity states how many grams of CO_{2}e are emitted per kWh of electricity and varies by region and hour. "
               "**Operational emissions** are the product of energy and carbon intensity, whereas **embodied emissions** arise from manufacturing the hardware; the latter are excluded here."))
    add(p_body("The CCF method, which builds on Etsy’s Cloud Jewels, estimates average power per vCPU from utilisation *u* as *P* = *P*_{min} + *u*(*P*_{max} − *P*_{min}), multiplies it by vCPU-hours, and adds terms for memory and networking [[ccf]]. "
               "The result is multiplied by the PUE and the grid emission factor; when utilisation is unknown, CCF falls back to 50 %. Such estimates are location-based; AWS’s Customer Carbon Footprint Tool also reports market-based figures "
               "and allocates the emissions of unused capacity proportionally to customers [[ccft]]. That matters for serverless: the simple model does not charge a 40 ms function for idle servers, but a provider-level view attributes some idle overhead to it. Sections 7.5 and 7.6 test how sensitive the conclusions are to this overhead."))
    add(p_body("The Software Carbon Intensity (SCI) specification, standardised as ISO/IEC 21031:2024, expresses emissions as a rate: SCI = ((*E* × *I*) + *M*) per *R*, where *E* is energy, *I* the carbon intensity, *M* the embodied emissions and *R* the functional unit [[scispec]]. "
               "This report uses an SCI-style indicator with *R* = 1,000 API requests (or one batch job), the boundary “compute and memory of the application tier” and *M* = 0."))
    add(p_h2("2.5 Carbon-aware computing and related work"))
    add(p_body("The carbon intensity of the grid fluctuates over the day with demand and with the share of variable renewables. Carbon-aware computing exploits this by running flexible work when, or where, electricity is cleaner."))
    add(p_body("Wiesner et al. analysed temporal workload shifting for several grids and found that the potential depends on the energy mix, the time constraints of the job and the accuracy of intensity forecasts; grids with much wind and solar offer large potential, "
               "whereas a largely nuclear grid such as France’s varies little [[wiesner]]. Google’s carbon-intelligent platform limits the hourly capacity of flexible workloads using day-ahead intensity forecasts so that they still finish within a day [[radovanovic]]. "
               "CCF provides open-source bottom-up estimation of cloud energy and emissions [[ccf]], AWS’s Customer Carbon Footprint Tool provides provider-level accounting [[ccft]], and the SCI specification provides a standard rate metric [[scispec]]; "
               "these supply the power coefficients, the idle-overhead question and the reporting unit of this report, and the first two works motivate the sweep parameters of Experiment 4."))
    add(p_body("Most of this work studies scheduling in isolation. Less often shown is a single application in which the deployment model, the compute configuration and the scheduling of delay-tolerant jobs are evaluated together with explicit, tested assumptions; this report addresses that gap at the scale of a university platform, within the limits of a simulation-based study."))

    # ============================================================ 3 Scenario and requirements
    add(p_h1("Scenario and Requirements"))
    add(p_h2("3.1 Requirements"))
    add(p_body("The platform serves the students of one university (UTC+8) from the AWS Tokyo region (ap-northeast-1); the stakeholders are students (fast, reliable access, also during exams), teachers (timely grading), the university’s IT department (low operating effort, predictable cost) and its sustainability office (measurable footprint). "
               "Students log in, browse the course catalogue and submit quizzes that combine ten multiple-choice questions with a short free-text answer. "
               "Two delay-tolerant jobs run behind the scenes: a nightly job that re-grades all submissions and builds reports, and the transcoding of newly uploaded lecture videos. "
               "@@T:t_req@@ lists the functional and non-functional requirements. Quantities that were not given by a real operator are assumptions and are marked as such."))
    tab("t_req", "Functional (F) and non-functional (N) requirements of the platform.",
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
    add(p_h2("3.2 Workload characterisation"))
    add(p_body("The daily request profile is based on the timetable of a typical campus: 1.4 % of the requests arrive between 00:00 and 06:00, 29.3 % between 06:00 and 12:00, 36.0 % between 12:00 and 18:00 and 33.3 % between 18:00 and 24:00. "
               "On an exam day the 14:00–16:00 window is weighted five times, so that 47.5 % of the day’s requests arrive in those two hours and the busiest hour carries 24.8 % of the daily volume instead of 8.0 %. "
               "@@T:t_work@@ translates the three scenarios into peak request rates and CPU demand, using the 4.2–4.3 ms of CPU per request that results from the measured endpoint times and the request mix (Section 6)."))
    tab("t_work", "Workload scenarios used in the evaluation.",
        ["Scenario", "Requests/day", "Busiest hour", "Peak rate (req/s)", "Peak CPU (vCPU)", "VM fleet (Design A)"],
        [["Campus, normal day", "300,000", "8.0 %", "6.7", "0.03", "2"],
         ["Campus, exam day", "900,000", "24.8 %", "62", "0.26", "2"],
         ["Large, exam day", "5,400,000", "24.8 %", "372", "1.56", "2"],
         ["Flash crowd (Exp. 8)", "+20,000 in 10 s", "–", "2,000", "12.7", "7 needed"]],
        [2300, 1500, 1200, 1400, 1300, 1314], align=["left", "center", "center", "center", "center", "center"])
    add(p_body("Two observations shape the design. First, even the large exam day needs only 1.56 vCPUs at its busiest hour, so a two-instance fleet (four vCPUs, the minimum for availability) is sufficient on average-rate grounds; "
               "the daily mean utilisation of that fleet is only 0.4–6.6 %. Second, the flash crowd at the start of an exam is a very different kind of load: 20,000 requests within 10 seconds need 12.7 vCPUs, three times the capacity of the minimal fleet. "
               "Average-rate sizing and burst sizing therefore lead to different answers, and this is the main reason for including the flash crowd in the evaluation."))
    add(p_h2("3.3 Service-level objectives and availability budget"))
    add(p_body("The availability target of 99.9 % per month allows 43.2 minutes of downtime in a 30-day month. To check whether the two designs can meet it, the published monthly uptime commitments of the AWS services on the request path were multiplied, "
               "assuming independent failures and a serial dependency (@@T:t_avail@@). These commitments are contractual floors backed by service credits, not measured availability, so the result is a conservative design check."))
    tab("t_avail", "Composite availability of the request path from AWS service-level commitments.",
        ["Request path", "Components (monthly uptime commitment)", "Composite", "Allowed downtime (30 days)"],
        [["Design A", "Load balancer 99.99 % × EC2 multi-AZ 99.99 % × RDS multi-AZ 99.95 %", "99.93 %", "30.2 min"],
         ["Design B via API gateway", "API gateway 99.95 % × Lambda 99.95 % × DynamoDB 99.99 %", "99.89 %", "47.5 min"],
         ["Design B via function URL", "Lambda 99.95 % × DynamoDB 99.99 %", "99.94 %", "25.9 min"],
         ["Target N3", "–", "99.90 %", "43.2 min"]],
        [2200, 3900, 1100, 1814], align=["left", "left", "center", "center"], bold_first_col=True)
    add(p_body("The commitments used are 99.99 % for the load balancer and for EC2 across two or more AZs, 99.95 % for RDS Multi-AZ, 99.95 % for the API gateway and Lambda, and 99.99 % for DynamoDB standard tables [[slaguide,slacloudonaut,slalambda,sladdb,slalist]]. "
               "The serverless design with an API gateway reaches 99.89 %, about four minutes per month short of the target, because two 99.95 % services are chained. Three remedies exist: invoke the function through a function URL "
               "or a CloudFront origin and so remove one link (99.94 %), let clients retry idempotent requests, or deploy a second region. The design in Section 4 uses the first two. "
               "The check also shows that availability is not an automatic advantage of either model: in this calculation the VM design is slightly ahead, and serverless needs a deliberate design to match it."))
    add(p_body("The evaluation is limited to the dynamic compute tier and the batch jobs; the static front-end, databases, object storage and data transfer are shared by both designs and excluded. Quantities not given by an operator are explicit assumptions (@@T:t_param@@), tested in Section 7.6. Students’ personal data must remain in the home region."))
