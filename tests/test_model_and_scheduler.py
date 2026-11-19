import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import carbon_model as cm, scheduler as sch, grid, core


def test_lambda_cost_matches_published_example():
    # Published worked example: 512 MB, 200 ms, 50M requests/month on x86 in us-east-1
    # costs $86.47 AFTER the free tier (1M requests + 400,000 GB-s).
    n = 50_000_000
    gross = n * cm.lambda_cost_usd(0.2, 512, "x86", api_gw=False)
    free = 1_000_000 * cm.LAMBDA_REQ_USD + 400_000 * cm.LAMBDA_GBS_USD["x86"]
    assert abs((gross - free) - 86.47) < 0.01


def test_arm_is_20pct_cheaper_on_duration():
    x = cm.lambda_billed_gbs(1.0, 1024) * cm.LAMBDA_GBS_USD["x86"]
    a = cm.lambda_billed_gbs(1.0, 1024) * cm.LAMBDA_GBS_USD["arm"]
    assert abs(a / x - 0.8) < 0.001


def test_cpu_bound_duration_scales_inverse_with_memory_until_one_vcpu():
    d1 = cm.lambda_duration_s(1.0, 0.0, 512); d2 = cm.lambda_duration_s(1.0, 0.0, 1024)
    assert abs(d1 / d2 - 2.0) < 1e-9
    assert cm.lambda_duration_s(1.0, 0.0, 3008) == cm.lambda_duration_s(1.0, 0.0, 1769)


def test_ec2_idle_energy():
    # 2 vCPU idle + 4 GB: (2*0.74 + 4*0.392) W * 1.135 = 3.4595 W
    assert abs(cm.ec2_energy_wh(1, 0.0) - 3.4595) < 1e-3


def test_carbon_unit_conversion():
    assert cm.carbon_g(1000, 400) == 400


def test_scheduler_picks_lowest_window_and_respects_deadline():
    f = np.array([9, 9, 9, 3, 3, 9, 9, 1, 1, 9], dtype=float)
    assert sch.best_start(f, 0, 2, 6) == 3          # [7,8] is outside deadline (last start = 4)
    assert sch.best_start(f, 0, 2, 10) == 7
    assert sch.best_start(f, 2, 2, 2) == 2          # zero flexibility -> run now


def test_scheduler_never_exceeds_deadline():
    rng = np.random.default_rng(0)
    for _ in range(200):
        f = rng.random(100); now = int(rng.integers(0, 40)); dur = int(rng.integers(1, 5)); dl = int(rng.integers(dur, 30))
        s = sch.best_start(f, now, dur, dl)
        assert now <= s <= now + dl - dur


def test_region_choice_prefers_clean_region_unless_penalised():
    fc = {"home": np.full(48, 400.0), "green": np.full(48, 30.0)}
    assert sch.best_region_start(fc, 0, 2, 10, home="home")[0] == "green"
    assert sch.best_region_start(fc, 0, 2, 10, home="home", move_penalty_g_per_kwh=500)[0] == "home"


def test_grid_series_is_deterministic():
    assert np.allclose(grid.actual_series("us-east-1", 2, seed=1), grid.actual_series("us-east-1", 2, seed=1))


def test_app_logic():
    assert core.grade_quiz(list("BDACABCDAB"))["mc_score"] == 10
    assert len(core.login("a", "b")["token"]) == 32
