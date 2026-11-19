# -*- coding: utf-8 -*-
REFS = {
 "masanet": "E. Masanet, A. Shehabi, N. Lei, S. Smith, J. Koomey, Recalibrating global data center energy-use estimates, Science 367 (6481) (2020) 984–986.",
 "barroso": "L.A. Barroso, U. Hölzle, The case for energy-proportional computing, IEEE Computer 40 (12) (2007) 33–37.",
 "ccf": "Cloud Carbon Footprint, Methodology (compute, memory, networking and PUE coefficients), https://www.cloudcarbonfootprint.org/docs/methodology/.",
 "sci": "Reconciling Bottom-Up Metrics with Top-Down Reporting for Cloud Carbon Accounting, arXiv:2610.10148, 2026 (survey of cloud carbon accounting and the SCI specification, ISO/IEC 21031).",
 "scispec": "Green Software Foundation, Software Carbon Intensity (SCI) Specification, ISO/IEC 21031:2024, https://sci.greensoftware.foundation/.",
 "nist": "P. Mell, T. Grance, The NIST Definition of Cloud Computing, NIST Special Publication 800-145, 2011.",
 "jonas": "E. Jonas et al., Cloud Programming Simplified: A Berkeley View on Serverless Computing, arXiv:1902.03383, 2019.",
 "lambdaprice": "Amazon Web Services, AWS Lambda pricing, https://aws.amazon.com/lambda/pricing/.",
 "lambdaex": "D. Volkov, Amazon Lambda Pricing: Cost Breakdown for 2026, Activepieces, 22 October 2026, https://www.activepieces.com/blog/amazon-lambda-pricing-cost-breakdown-for-2026.",
 "graviton": "Amazon Web Services, AWS Lambda functions powered by AWS Graviton2 processor: run your functions on Arm and get up to 34% better price performance, AWS News Blog, https://aws.amazon.com/blogs/aws/aws-lambda-functions-powered-by-aws-graviton2-processor-run-your-functions-on-arm-and-get-up-to-34-better-price-performance/.",
 "lambdalimits": "Amazon Web Services, Lambda quotas (function memory, CPU allocation and timeout), AWS Lambda Developer Guide, https://docs.aws.amazon.com/lambda/latest/dg/limits.html.",
 "ec2": "Amazon Web Services, Amazon EC2 T3 instances (on-demand pricing), https://aws.amazon.com/ec2/instance-types/t3/.",
 "t3price": "DevZero, AWS EC2 t3.medium pricing (on-demand and 1-year reserved), https://www.devzero.io/instances/aws/t3.medium.",
 "t4gprice": "Economize, AWS t4g.medium pricing (on-demand and reserved), https://www.economize.cloud/resources/aws/pricing/ec2/t4g.medium/.",
 "alb": "Amazon Web Services, Elastic Load Balancing pricing (Application Load Balancer hourly and LCU charges), https://aws.amazon.com/elasticloadbalancing/classicloadbalancer/pricing.",
 "pue": "Amazon Web Services, Power Usage Effectiveness (PUE) Methodology, Amazon Sustainability, December 2024, https://sustainability.aboutamazon.com/pue-methodology.pdf.",
 "ccft": "M. O’Toole, A. Bateman, M. Fraga, P. Csatlos, Updated Carbon Methodology for the AWS Customer Carbon Footprint Tool, AWS Cloud Financial Management Blog, https://aws.amazon.com/blogs/aws-cloud-financial-management/updated-carbon-methodology-for-the-aws-customer-carbon-footprint-tool.",
 "wiesner": "P. Wiesner, I. Behnke, D. Scheinert, K. Gontarska, L. Thamsen, Let’s Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud, Proc. 22nd Int. Middleware Conf. (Middleware ’21), ACM, 2021, doi:10.1145/3464298.3493399.",
 "radovanovic": "A. Radovanović, R. Koningstein, I. Schneider, B. Chen, A. Duarte, B. Roy, D. Xiao et al., Carbon-Aware Computing for Datacenters, arXiv:2106.11750, 2021.",
 "slalambda": "Amazon Web Services, AWS Lambda Service Level Agreement, https://aws.amazon.com/lambda/sla.",
 "sladdb": "Amazon Web Services, Amazon DynamoDB Service Level Agreement, https://aws.amazon.com/dynamodb/sla.",
 "slaguide": "AWS Builder Center, Understanding AWS Service Level Agreements (SLAs): a practical guide for builders, https://builder.aws.com/content/3KPIdrMbWaZJrWsXnmY0YpuUYaA/understanding-aws-service-level-agreements-slas-a-practical-guide-for-builders.",
 "slacloudonaut": "cloudonaut, AWS SLA: Are you able to keep your availability promise?, https://cloudonaut.io/aws-sla-are-you-able-to-keep-your-availability-promise/.",
 "slalist": "mikaelvesavuori, cloud-sla: overview of cloud provider SLAs (Amazon Elastic Load Balancing, 99.99 %), https://github.com/mikaelvesavuori/cloud-sla.",
}
TITLE = ["Carbon-Aware Cloud Architecture for an", "Online Education Platform: Serverless", "vs. VM Design, Prototype and Evaluation"]
KEYWORDS = "cloud architecture design; serverless computing; AWS Lambda; carbon-aware scheduling; green cloud; energy estimation; software carbon intensity"
ABSTRACT = ("Cloud architectures are usually judged on cost, availability and performance, while the carbon emissions they cause stay invisible. "
 "This report treats carbon as a first-class design requirement for an online education platform (login, course catalogue, quizzes, nightly grading and lecture-video transcoding). "
 "Two architectures are designed and compared: Design A, a traditional deployment on two always-on EC2 instances behind a load balancer, and Design B, a serverless deployment on AWS Lambda (arm64) "
 "with a carbon-aware scheduler for delay-tolerant batch jobs. The report covers requirements, security, reliability and observability design, technology selection, and a Python prototype with a cost–energy–carbon model "
 "based on the Cloud Carbon Footprint methodology and public AWS prices. The CPU cost of each endpoint was measured, and both designs were evaluated by discrete-event simulation in eight experiments, including a sensitivity analysis, "
 "stronger VM baselines (Arm and reserved instances) and an exam-start flash crowd. For a 10,000-student campus, Design B reduces daily cost by 85 % and estimated emissions by 99 % while meeting a 100 ms latency target, "
 "and it stays at least 11 times lower in emissions in every one-at-a-time sensitivity case. The cost advantage ends at about 2.4 million requests per day (1.3 million against the cheapest VM baseline). "
 "A flash crowd shows the value of elasticity: two VMs missed the latency target for 99.6 % of burst requests, whereas Lambda missed it for 3.4 % because of cold starts. Shifting nightly jobs in time saves 4–17 % of emissions and moving them to a low-carbon region 88–94 %, "
 "but only where data-protection rules allow it. Energy is estimated rather than measured and grid profiles are synthetic, so AWS validation with real data remains future work.")
