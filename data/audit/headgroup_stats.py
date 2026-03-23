"""AUDIT 4: Headgroup statistics — DOTAP vs DDAB significance.

Tests whether the claimed DOTAP > DDAB difference is statistically
significant using Mann-Whitney U test and bootstrap confidence intervals.

Exploration script — no tests needed.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu, shapiro, ttest_ind

_ROOT = Path(__file__).resolve().parent.parent.parent
_KIM_SCREEN = _ROOT / "data" / "kim_screen" / "kim_2024_screen_corrected.json"


def _load_headgroup_data() -> dict[str, list[float]]:
    """Load Kim screen data grouped by helper lipid."""
    with open(_KIM_SCREEN) as f:
        screen = json.load(f)

    groups: dict[str, list[float]] = {}
    for fm in screen["formulations"]:
        hl = fm.get("helper_lipid_name")
        bm = fm.get("bm_normalized_bc")
        if hl is None or bm is None:
            continue
        groups.setdefault(hl, []).append(float(bm))

    return groups


def _descriptive_stats(groups: dict[str, list[float]]) -> None:
    """Print descriptive statistics for each helper lipid group."""
    print("\n" + "=" * 70)
    print("DESCRIPTIVE STATISTICS BY HELPER LIPID")
    print("=" * 70)

    hdr = (
        f"{'Helper':>12s} {'N':>4s} {'Mean':>8s} {'Median':>8s} "
        f"{'SD':>8s} {'Min':>6s} {'Max':>6s}"
    )
    print(hdr)
    print("-" * len(hdr))

    for hl in sorted(groups):
        vals = groups[hl]
        arr = np.array(vals)
        print(
            f"{hl:>12s} {len(vals):4d} {arr.mean():8.2f} "
            f"{np.median(arr):8.2f} {arr.std():8.2f} "
            f"{arr.min():6.1f} {arr.max():6.1f}"
        )


def _mann_whitney_test(groups: dict[str, list[float]]) -> None:
    """Run Mann-Whitney U test for DOTAP vs each other helper."""
    print("\n" + "=" * 70)
    print("MANN-WHITNEY U TEST: DOTAP vs OTHERS")
    print("=" * 70)

    dotap = groups.get("DOTAP", [])
    if not dotap:
        print("  ERROR: No DOTAP data found!")
        return

    for hl in sorted(groups):
        if hl == "DOTAP":
            continue
        other = groups[hl]
        if len(other) < 3:
            print(f"  DOTAP vs {hl}: skipped (n={len(other)} < 3)")
            continue

        stat, p = mannwhitneyu(
            dotap, other, alternative="greater",
        )
        effect_size = stat / (len(dotap) * len(other))
        print(
            f"\n  DOTAP (n={len(dotap)}) vs {hl} (n={len(other)}):"
        )
        print(
            f"    U={stat:.1f}, p={p:.6f}, "
            f"rank-biserial r={effect_size:.3f}"
        )
        print(
            f"    {'SIGNIFICANT' if p < 0.05 else 'NOT SIGNIFICANT'} "
            f"at alpha=0.05"
        )

    # Also test DOTAP vs all non-DOTAP combined
    non_dotap = []
    for hl, vals in groups.items():
        if hl != "DOTAP":
            non_dotap.extend(vals)

    if non_dotap:
        stat, p = mannwhitneyu(
            dotap, non_dotap, alternative="greater",
        )
        print(
            f"\n  DOTAP (n={len(dotap)}) vs ALL others "
            f"(n={len(non_dotap)}):"
        )
        print(f"    U={stat:.1f}, p={p:.6f}")
        print(
            f"    {'SIGNIFICANT' if p < 0.05 else 'NOT SIGNIFICANT'} "
            f"at alpha=0.05"
        )


def _normality_check(groups: dict[str, list[float]]) -> None:
    """Check normality assumption for t-test validity."""
    print("\n" + "=" * 70)
    print("NORMALITY CHECK (Shapiro-Wilk)")
    print("=" * 70)

    for hl in sorted(groups):
        vals = groups[hl]
        if len(vals) < 3:
            print(f"  {hl}: skipped (n={len(vals)} < 3)")
            continue
        stat, p = shapiro(vals)
        normal = "Normal" if p > 0.05 else "NOT normal"
        print(f"  {hl}: W={stat:.4f}, p={p:.6f} → {normal}")

    print("\n  NOTE: If data is non-normal, Mann-Whitney U is the correct")
    print("  test (not t-test). We use it as the primary test.")


def _welch_t_test(groups: dict[str, list[float]]) -> None:
    """Run Welch's t-test as secondary comparison."""
    print("\n" + "=" * 70)
    print("WELCH'S T-TEST (secondary, for comparison)")
    print("=" * 70)

    dotap = groups.get("DOTAP", [])
    if not dotap:
        return

    for hl in sorted(groups):
        if hl == "DOTAP":
            continue
        other = groups[hl]
        if len(other) < 3:
            continue

        stat, p = ttest_ind(dotap, other, equal_var=False)
        print(
            f"  DOTAP vs {hl}: t={stat:.3f}, p={p:.6f} "
            f"({'SIG' if p < 0.05 else 'NS'})"
        )


def _bootstrap_ci(groups: dict[str, list[float]]) -> None:
    """Bootstrap 95% CI for mean difference DOTAP - DDAB."""
    print("\n" + "=" * 70)
    print("BOOTSTRAP 95% CI: DOTAP mean - DDAB mean")
    print("=" * 70)

    dotap = np.array(groups.get("DOTAP", []))
    ddab = np.array(groups.get("DDAB", []))

    if len(dotap) < 3 or len(ddab) < 3:
        print("  Insufficient data for bootstrap")
        return

    observed_diff = dotap.mean() - ddab.mean()
    print(f"  Observed difference: {observed_diff:.2f}")

    rng = np.random.default_rng(42)
    n_boot = 10000
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        d_samp = rng.choice(dotap, size=len(dotap), replace=True)
        b_samp = rng.choice(ddab, size=len(ddab), replace=True)
        diffs[i] = d_samp.mean() - b_samp.mean()

    ci_lo = float(np.percentile(diffs, 2.5))
    ci_hi = float(np.percentile(diffs, 97.5))
    print(f"  Bootstrap 95% CI: [{ci_lo:.2f}, {ci_hi:.2f}]")
    if ci_lo > 0:
        print("  CI excludes zero — difference is significant")
    else:
        print(
            "  CI includes zero — difference may not be significant"
        )


def _outlier_check(groups: dict[str, list[float]]) -> None:
    """Check for outliers that might drive the DOTAP effect."""
    print("\n" + "=" * 70)
    print("OUTLIER CHECK: DOTAP group")
    print("=" * 70)

    dotap = np.array(groups.get("DOTAP", []))
    if len(dotap) < 4:
        print("  Too few data points for outlier analysis")
        return

    q1 = float(np.percentile(dotap, 25))
    q3 = float(np.percentile(dotap, 75))
    iqr = q3 - q1
    lo = q1 - 1.5 * iqr
    hi = q3 + 1.5 * iqr

    outliers = dotap[(dotap < lo) | (dotap > hi)]
    print(f"  Q1={q1:.1f}, Q3={q3:.1f}, IQR={iqr:.1f}")
    print(f"  Outlier bounds: [{lo:.1f}, {hi:.1f}]")
    print(f"  Outliers: {len(outliers)} values: {outliers}")

    if len(outliers) > 0:
        # Re-test without outliers
        clean = dotap[(dotap >= lo) & (dotap <= hi)]
        ddab = np.array(groups.get("DDAB", []))
        if len(ddab) >= 3 and len(clean) >= 3:
            stat, p = mannwhitneyu(
                clean.tolist(), ddab.tolist(),
                alternative="greater",
            )
            print(
                f"\n  Without outliers: DOTAP (n={len(clean)}) "
                f"vs DDAB (n={len(ddab)})"
            )
            print(
                f"    U={stat:.1f}, p={p:.6f} "
                f"({'SIG' if p < 0.05 else 'NS'})"
            )
            print(
                f"    Clean DOTAP mean: {clean.mean():.2f} "
                f"(was {dotap.mean():.2f})"
            )


def _peg_chain_confound(groups: dict[str, list[float]]) -> None:
    """Check if PEG chain confounds the DOTAP vs DDAB difference."""
    print("\n" + "=" * 70)
    print("CONFOUND CHECK: PEG chain × helper lipid interaction")
    print("=" * 70)

    with open(_KIM_SCREEN) as f:
        screen = json.load(f)

    # Cross-tabulate helper × PEG × BM
    cross: dict[tuple[str, str], list[float]] = {}
    for fm in screen["formulations"]:
        hl = fm.get("helper_lipid_name")
        peg = fm.get("peg_chain")
        bm = fm.get("bm_normalized_bc")
        if hl is None or peg is None or bm is None:
            continue
        cross.setdefault((hl, peg), []).append(float(bm))

    hdr = f"{'Helper':>12s} {'PEG':>6s} {'N':>4s} {'Mean BM':>8s}"
    print(hdr)
    print("-" * len(hdr))
    for (hl, peg), vals in sorted(cross.items()):
        print(
            f"{hl:>12s} {peg:>6s} {len(vals):4d} "
            f"{np.mean(vals):8.2f}"
        )

    # Is DOTAP effect consistent across PEG chains?
    print("\n  DOTAP effect within each PEG chain:")
    for peg_name in ["C14", "C18"]:
        dotap_vals = cross.get(("DOTAP", peg_name), [])
        ddab_vals = cross.get(("DDAB", peg_name), [])
        if len(dotap_vals) >= 3 and len(ddab_vals) >= 3:
            stat, p = mannwhitneyu(
                dotap_vals, ddab_vals, alternative="greater",
            )
            print(
                f"    PEG {peg_name}: DOTAP mean="
                f"{np.mean(dotap_vals):.2f} vs "
                f"DDAB mean={np.mean(ddab_vals):.2f} "
                f"(p={p:.4f})"
            )
        else:
            print(
                f"    PEG {peg_name}: insufficient data "
                f"(DOTAP n={len(dotap_vals)}, "
                f"DDAB n={len(ddab_vals)})"
            )


def main() -> None:
    """Run headgroup statistics audit."""
    print("=" * 70)
    print("AUDIT 4: HEADGROUP STATISTICS — DOTAP vs DDAB")
    print("=" * 70)

    groups = _load_headgroup_data()
    print(f"  Helper lipids found: {sorted(groups.keys())}")
    print(
        f"  Total observations: "
        f"{sum(len(v) for v in groups.values())}"
    )

    _descriptive_stats(groups)
    _normality_check(groups)
    _mann_whitney_test(groups)
    _welch_t_test(groups)
    _bootstrap_ci(groups)
    _outlier_check(groups)
    _peg_chain_confound(groups)

    # Final verdict
    print("\n" + "=" * 70)
    print("AUDIT 4 SUMMARY")
    print("=" * 70)
    dotap = groups.get("DOTAP", [])
    ddab = groups.get("DDAB", [])
    if dotap and ddab:
        print(f"  DOTAP mean BM: {np.mean(dotap):.2f}")
        print(f"  DDAB mean BM: {np.mean(ddab):.2f}")
        print(
            f"  Difference: {np.mean(dotap) - np.mean(ddab):.2f} "
            f"({np.mean(dotap)/max(np.mean(ddab), 0.01):.1f}x)"
        )


if __name__ == "__main__":
    main()
