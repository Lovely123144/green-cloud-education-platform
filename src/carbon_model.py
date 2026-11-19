"""Cost / energy / carbon model for Design A (EC2 + ALB) and Design B (Lambda).

Energy follows the Cloud Carbon Footprint (CCF) / Cloud Jewels method:
    avg_watts = W_MIN + utilisation * (W_MAX - W_MIN)         [per vCPU]
    energy    = (vcpus * avg_watts + mem_GB * W_MEM) * hours * PUE
    carbon    = energy[kWh] * grid_intensity[gCO2e/kWh]
Pricing constants are public on-demand list prices (us-east-1, 2026).
"""
import math

# ---- power model (Cloud Carbon Footprint, AWS averages) --------------------
W_MIN, W_MAX = 0.74, 3.5          # W per vCPU at 0 % / 100 % utilisation
W_MEM_PER_GB = 0.392              # W per GB of memory
PUE = 1.135                       # AWS-wide PUE used by CCF
DEFAULT_UTIL = 0.5                # CCF fallback when utilisation is unknown

# ---- AWS Lambda -------------------------------------------------------------
MB_PER_VCPU = 1769                # Lambda: 1,769 MB memory == 1 vCPU
LAMBDA_REQ_USD = 0.20 / 1e6
LAMBDA_GBS_USD = {"x86": 0.0000166667, "arm": 0.0000133334}
API_GW_REQ_USD = 1.00 / 1e6       # API Gateway HTTP API (assumption, verify)

# ---- EC2 / load balancer ----------------------------------------------------
EC2_USD_HR = 0.0416               # t3.medium (2 vCPU, 4 GiB)
EC2_VCPU, EC2_MEM_GB = 2, 4
ALB_USD_HR, ALB_LCU_USD_HR = 0.0225, 0.008


def avg_watts_per_vcpu(util: float) -> float:
    return W_MIN + util * (W_MAX - W_MIN)


# ---------------------------- Lambda ---------------------------------------
def lambda_duration_s(cpu_s_at_1vcpu: float, io_s: float, mem_mb: int) -> float:
    """Warm execution time. CPU work scales with the CPU share (memory/1769,
    capped at 1 vCPU for single-threaded code); I/O wait does not."""
    share = min(mem_mb / MB_PER_VCPU, 1.0)
    return cpu_s_at_1vcpu / share + io_s


def lambda_billed_gbs(duration_s: float, mem_mb: int) -> float:
    return math.ceil(duration_s * 1000) / 1000 * mem_mb / 1024   # 1 ms granularity


def lambda_cost_usd(duration_s, mem_mb, arch="arm", api_gw=True) -> float:
    c = LAMBDA_REQ_USD + lambda_billed_gbs(duration_s, mem_mb) * LAMBDA_GBS_USD[arch]
    return c + (API_GW_REQ_USD if api_gw else 0.0)


def lambda_energy_wh(duration_s, mem_mb, util=DEFAULT_UTIL, idle_factor=1.0) -> float:
    """idle_factor >= 1 models provider-side idle/warm capacity attributed to the tenant."""
    vcpu = mem_mb / MB_PER_VCPU
    watts = vcpu * avg_watts_per_vcpu(util) + (mem_mb / 1024) * W_MEM_PER_GB
    return watts * duration_s / 3600 * PUE * idle_factor


# ---------------------------- EC2 ------------------------------------------
def ec2_energy_wh(hours, util, n=1) -> float:
    watts = EC2_VCPU * avg_watts_per_vcpu(util) + EC2_MEM_GB * W_MEM_PER_GB
    return n * watts * hours * PUE


def ec2_cost_usd(hours, n=1, lcu=1.0) -> float:
    return n * EC2_USD_HR * hours + (ALB_USD_HR + lcu * ALB_LCU_USD_HR) * hours


# ---------------------------- generic batch compute -------------------------
def batch_energy_wh(vcpus, hours, util=0.9, mem_gb_per_vcpu=2.0) -> float:
    watts = vcpus * (avg_watts_per_vcpu(util) + mem_gb_per_vcpu * W_MEM_PER_GB)
    return watts * hours * PUE


def carbon_g(energy_wh: float, intensity_g_per_kwh: float) -> float:
    return energy_wh / 1000.0 * intensity_g_per_kwh
