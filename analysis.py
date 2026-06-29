"""
analysis.py — core statistical logic for A/B test significance analyser.
No UI dependencies. All functions return plain dicts or scalars.
"""

import math
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.power import NormalIndPower


def run_ab_test(
    control_visitors: int,
    control_conversions: int,
    test_visitors: int,
    test_conversions: int,
    alpha: float = 0.05,
) -> dict:
    """
    Run a two-proportion z-test comparing control vs test variant.

    Parameters
    ----------
    control_visitors     : total users in control group
    control_conversions  : converting users in control group
    test_visitors        : total users in test group
    test_conversions     : converting users in test group
    alpha                : significance level (default 0.05 -> 95% confidence)

    Returns
    -------
    dict with keys:
        control_rate, test_rate, absolute_diff, relative_uplift,
        z_stat, p_value, significant, ci_lower, ci_upper, alpha
    """
    if control_visitors <= 0 or test_visitors <= 0:
        raise ValueError("Visitor counts must be greater than zero.")
    if control_conversions > control_visitors or test_conversions > test_visitors:
        raise ValueError("Conversions cannot exceed visitors.")

    p1 = control_conversions / control_visitors
    p2 = test_conversions / test_visitors

    # Pooled proportion for z-test standard error
    p_pool = (control_conversions + test_conversions) / (control_visitors + test_visitors)
    se_pooled = math.sqrt(p_pool * (1 - p_pool) * (1 / control_visitors + 1 / test_visitors))

    z_stat = (p2 - p1) / se_pooled if se_pooled > 0 else 0.0
    p_value = float(stats.norm.sf(abs(z_stat)) * 2)  # two-tailed

    # 95% CI on the difference using unpooled SE
    z_crit = stats.norm.ppf(1 - alpha / 2)
    se_unpooled = math.sqrt(p1 * (1 - p1) / control_visitors + p2 * (1 - p2) / test_visitors)
    diff = p2 - p1
    ci_lower = diff - z_crit * se_unpooled
    ci_upper = diff + z_crit * se_unpooled

    relative_uplift = (diff / p1 * 100) if p1 > 0 else 0.0

    return {
        "control_rate": p1,
        "test_rate": p2,
        "absolute_diff": diff,
        "relative_uplift": relative_uplift,
        "z_stat": z_stat,
        "p_value": p_value,
        "significant": p_value < alpha,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "alpha": alpha,
    }


def calculate_sample_size(
    baseline_rate: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> dict:
    """
    Calculate minimum required sample size per variant for an A/B test.

    Parameters
    ----------
    baseline_rate : current conversion rate (e.g. 0.03 for 3%)
    mde           : minimum detectable effect as relative uplift (e.g. 0.10 for 10%)
    alpha         : significance level (default 0.05)
    power         : desired statistical power (default 0.80)

    Returns
    -------
    dict with keys:
        baseline_rate, target_rate, mde, alpha, power,
        per_variant, total, effect_size
    """
    if not (0 < baseline_rate < 1):
        raise ValueError("baseline_rate must be between 0 and 1.")
    if mde <= 0:
        raise ValueError("MDE must be greater than zero.")

    target_rate = baseline_rate * (1 + mde)
    target_rate = min(target_rate, 0.9999)

    effect_size = proportion_effectsize(baseline_rate, target_rate)
    analysis = NormalIndPower()
    n = analysis.solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        alternative="two-sided",
    )
    per_variant = math.ceil(n)

    return {
        "baseline_rate": baseline_rate,
        "target_rate": target_rate,
        "mde": mde,
        "alpha": alpha,
        "power": power,
        "per_variant": per_variant,
        "total": per_variant * 2,
        "effect_size": effect_size,
    }


if __name__ == "__main__":
    # Quick sanity check — Cookie Cats A/B test (gate_30 vs gate_40, 7-day retention)
    # Approximate published figures
    result = run_ab_test(
        control_visitors=44700,
        control_conversions=8502,
        test_visitors=45489,
        test_conversions=8279,
    )
    print("=== Cookie Cats A/B Test (7-day retention) ===")
    print(f"  Control rate : {result['control_rate']:.4f}")
    print(f"  Test rate    : {result['test_rate']:.4f}")
    print(f"  Uplift       : {result['relative_uplift']:.2f}%")
    print(f"  p-value      : {result['p_value']:.4f}")
    print(f"  Significant  : {result['significant']}")
    print(f"  95% CI       : [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")

    print()

    sample = calculate_sample_size(baseline_rate=0.19, mde=0.05, alpha=0.05, power=0.80)
    print("=== Sample Size Calculator ===")
    print(f"  Baseline rate  : {sample['baseline_rate']:.0%}")
    print(f"  Target rate    : {sample['target_rate']:.2%}")
    print(f"  Per variant    : {sample['per_variant']:,}")
    print(f"  Total required : {sample['total']:,}")
