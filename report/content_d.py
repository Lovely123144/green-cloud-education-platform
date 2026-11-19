# -*- coding: utf-8 -*-
import os
import pandas as pd
from docx_lib import *
from content_b import excerpt

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def part_d(add, fig, tab):
    # ---------------------------------------------------------------- Appendix C
    add(p_h1("Appendix A. Reproduction and Deployment Guide", numbered=False))
    add(p_body("The experiments run on any machine with Python 3 and need no cloud account (the measured CPU times are stored in a results file; re-measuring on another machine changes all numbers slightly):"))
    add(p_code(["pip install -r requirements.txt",
                "python3 -m pytest -q tests          # 10 unit tests",
                "python3 sim/run_experiments.py      # eight experiments -> results/*.csv, *.json",
                "python3 sim/make_figures.py         # figures -> figures/*.png"]))
    add(p_body("To turn the simulation into a measurement: deploy Design B with the SAM template and start Design A as two t3.medium instances behind an Application Load Balancer (set a billing alarm first); run the Locust load test against both with identical user numbers, "
               "including a burst profile; read duration, billed duration and memory from the Lambda report lines and CPU utilisation from the instance metrics and recompute energy with Equations 1–5; replace the synthetic grid profiles by hourly data from an intensity service "
               "and re-run Experiments 3 and 4; and check the account’s Lambda concurrency quota and provisioned concurrency for the exam start."))
    add(p_h1("Appendix B. Glossary", numbered=False, page_break=True))
    tab("t_gloss", "Terms and abbreviations used in this report.",
        ["Term", "Meaning"],
        [["AZ / Region", "Availability Zone: separate data-centre group inside a Region; Region: isolated geographic area of the provider"],
         ["Cold start", "Delay when a function request needs a new execution environment"],
         ["CCF", "Cloud Carbon Footprint, an open-source method for estimating cloud energy and emissions"],
         ["FaaS / IaaS / PaaS / SaaS", "Function / infrastructure / platform / software as a service"],
         ["GB-second", "One gigabyte of configured memory used for one second; Lambda’s duration billing unit"],
         ["Graviton / arm64", "AWS’s Arm-based processors; Lambda price per GB-second is about 20 % lower than x86"],
         ["gCO₂e", "Grams of carbon-dioxide equivalent"],
         ["Grid intensity", "Grams of CO_{2}e emitted per kWh of electricity in a region and hour"],
         ["p50 / p95 / p99", "Median, 95th and 99th percentile of latency"],
         ["PUE", "Power usage effectiveness: facility energy divided by IT equipment energy"],
         ["RPO / RTO", "Recovery point / time objective: tolerated data loss and downtime after a failure"],
         ["SCI", "Software Carbon Intensity: ((E × I) + M) per R, ISO/IEC 21031:2024"],
         ["SLA / SLO", "Service-level agreement (contract) / objective (target)"],
         ["vCPU", "Virtual CPU; on Lambda, 1,769 MB of memory corresponds to one vCPU"],
         ["WAF", "Web application firewall"]],
        [2400, 6614], align=["left", "left"], bold_first_col=True)
