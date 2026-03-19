"""Tests for therapeutic window analysis module."""

from __future__ import annotations

import json
from pathlib import Path

from lnp_optimizer.therapeutic_window import (
    DoseResponseFit,
    ParetoPoint,
    TherapeuticWindow,
    _compute_ecx,
    compute_correlation,
    compute_pareto_frontier,
    compute_therapeutic_window,
    fit_dose_response,
)
from lnp_optimizer.tw_pipeline import (
    identify_gaps,
    load_paired_data,
    model_dex_intervention,
    model_glycolipid_intervention,
    run_full_analysis,
)

# ── Dose-response fitting tests ──────────────────────────────────────────


class TestDoseResponse:
    """Tests for 4PL dose-response fitting."""

    def test_fit_known_sigmoid(self) -> None:
        """Fit recovers known sigmoid parameters."""
        doses = [0.1, 0.3, 1.0, 3.0, 10.0]
        # Generate data from known 4PL: top=100, ec50=1.0, hill=1.0
        responses = [100.0 / (1 + (1.0 / d) ** 1.0) for d in doses]
        fit = fit_dose_response(doses, responses, name="test")

        assert fit.error is None
        assert abs(fit.ec50 - 1.0) < 0.1
        assert abs(fit.top - 100.0) < 5.0
        assert fit.r_squared > 0.99

    def test_fit_fixed_top(self) -> None:
        """Fixed top=100 with few data points."""
        fit = fit_dose_response(
            [0.5, 1.0, 2.0], [12, 23, 35],
            name="kim_lnp67", fix_top=100.0,
        )
        assert fit.error is None
        assert fit.fixed_top is True
        assert fit.top == 100.0
        assert fit.ec50 > 0

    def test_fit_free_top(self) -> None:
        """Free top with enough data points."""
        fit = fit_dose_response(
            [0.25, 0.5, 1.0, 2.0, 4.0], [15, 22, 25, 38, 72],
            name="kim_human",
        )
        assert fit.error is None
        assert fit.fixed_top is False
        assert fit.top > 50

    def test_ec30_computed(self) -> None:
        """EC30 is computed when top > 30."""
        fit = fit_dose_response(
            [0.05, 0.25], [10, 55],
            name="breda", fix_top=100.0,
        )
        assert fit.ec30 is not None
        assert fit.ec30 > 0

    def test_ec30_none_when_top_below_30(self) -> None:
        """EC30 is None when maximum efficacy < 30%."""
        result = _compute_ecx(top=25.0, ec50=1.0, hill=1.0, target=30.0)
        assert result is None

    def test_r_squared_perfect_fit(self) -> None:
        """R² = 1.0 for 2-point fit with fixed top."""
        fit = fit_dose_response(
            [0.3, 1.0], [75, 90],
            name="shi", fix_top=100.0,
        )
        assert fit.r_squared == 1.0

    def test_dose_response_dataclass_fields(self) -> None:
        """DoseResponseFit has all expected fields."""
        fit = fit_dose_response(
            [0.5, 1.0], [20, 40], name="test", fix_top=100.0,
        )
        assert hasattr(fit, "ec50")
        assert hasattr(fit, "hill")
        assert hasattr(fit, "top")
        assert hasattr(fit, "bottom")
        assert hasattr(fit, "r_squared")
        assert hasattr(fit, "ec30")
        assert hasattr(fit, "doses")
        assert hasattr(fit, "responses")

    def test_antibody_more_potent_than_untargeted(self) -> None:
        """Antibody EC50 < untargeted EC50."""
        breda = fit_dose_response(
            [0.05, 0.25], [10, 55], name="breda", fix_top=100.0,
        )
        kim = fit_dose_response(
            [0.5, 1.0, 2.0], [12, 23, 35], name="kim", fix_top=100.0,
        )
        assert breda.ec50 < kim.ec50


# ── Pareto frontier tests ────────────────────────────────────────────────


class TestParetoFrontier:
    """Tests for Pareto frontier computation."""

    def test_single_point_is_pareto(self) -> None:
        """Single point is always Pareto-optimal."""
        points = [ParetoPoint("A", 50.0, 10.0, 5.0, "test")]
        result = compute_pareto_frontier(points)
        assert result[0].is_pareto is True

    def test_dominated_point_excluded(self) -> None:
        """Dominated point is not Pareto-optimal."""
        points = [
            ParetoPoint("A", 50.0, 10.0, 5.0, "test"),
            ParetoPoint("B", 30.0, 20.0, 1.5, "test"),  # dominated by A
        ]
        result = compute_pareto_frontier(points)
        assert result[0].is_pareto is True  # A
        assert result[1].is_pareto is False  # B

    def test_tradeoff_points_both_pareto(self) -> None:
        """Points with different tradeoffs are both Pareto-optimal."""
        points = [
            ParetoPoint("A", 50.0, 50.0, 1.0, "test"),  # high BM, high liver
            ParetoPoint("B", 10.0, 2.0, 5.0, "test"),   # low BM, low liver
        ]
        result = compute_pareto_frontier(points)
        assert result[0].is_pareto is True
        assert result[1].is_pareto is True

    def test_identical_points(self) -> None:
        """Identical points don't dominate each other."""
        points = [
            ParetoPoint("A", 50.0, 10.0, 5.0, "test"),
            ParetoPoint("B", 50.0, 10.0, 5.0, "test"),
        ]
        result = compute_pareto_frontier(points)
        assert result[0].is_pareto is True
        assert result[1].is_pareto is True

    def test_known_pareto_from_data(self) -> None:
        """Known Pareto structure from Kim/Breda data."""
        points = [
            ParetoPoint("CD117/LNP", 55.0, 76.0, 0.72, "breda"),
            ParetoPoint("LNP67", 20.9, 20.1, 1.04, "kim_E2"),
            ParetoPoint("LNP108", 8.8, 1.6, 5.5, "kim_E2"),
            ParetoPoint("LP01", 5.0, 42.4, 0.12, "kim_E2"),
        ]
        result = compute_pareto_frontier(points)
        # CD117 (highest BM), LNP108 (lowest liver), LNP67 (middle)
        names_pareto = {p.formulation for p in result if p.is_pareto}
        assert "CD117/LNP" in names_pareto  # highest BM
        assert "LNP108" in names_pareto      # lowest liver
        assert "LP01" not in names_pareto     # dominated

    def test_empty_list(self) -> None:
        """Empty list returns empty list."""
        result = compute_pareto_frontier([])
        assert result == []


# ── Correlation tests ────────────────────────────────────────────────────


class TestCorrelation:
    """Tests for BM-liver correlation computation."""

    def test_perfect_positive_correlation(self) -> None:
        """Perfectly correlated data gives r ≈ 1."""
        points = [
            ParetoPoint("A", 10.0, 10.0, 1.0, "test"),
            ParetoPoint("B", 20.0, 20.0, 1.0, "test"),
            ParetoPoint("C", 30.0, 30.0, 1.0, "test"),
        ]
        corr = compute_correlation(points)
        assert abs(corr["pearson_r"] - 1.0) < 0.01

    def test_uncorrelated_data(self) -> None:
        """Uncorrelated data gives |r| < 0.5."""
        points = [
            ParetoPoint("A", 10.0, 30.0, 0.33, "test"),
            ParetoPoint("B", 50.0, 10.0, 5.0, "test"),
            ParetoPoint("C", 30.0, 50.0, 0.6, "test"),
            ParetoPoint("D", 20.0, 15.0, 1.33, "test"),
            ParetoPoint("E", 40.0, 45.0, 0.89, "test"),
        ]
        corr = compute_correlation(points)
        assert abs(corr["pearson_r"]) < 0.5

    def test_correlation_returns_all_keys(self) -> None:
        """Correlation dict has all expected keys."""
        points = [
            ParetoPoint("A", 10.0, 10.0, 1.0, "test"),
            ParetoPoint("B", 20.0, 20.0, 1.0, "test"),
            ParetoPoint("C", 30.0, 30.0, 1.0, "test"),
        ]
        corr = compute_correlation(points)
        assert "pearson_r" in corr
        assert "pearson_p" in corr
        assert "spearman_r" in corr
        assert "spearman_p" in corr


# ── Therapeutic window tests ─────────────────────────────────────────────


class TestTherapeuticWindow:
    """Tests for therapeutic window computation."""

    def test_hsc_liver_ratio(self) -> None:
        """HSC:liver ratio computed correctly."""
        fit = DoseResponseFit(
            name="test", ec50=0.2, hill=1.5, top=100, bottom=0,
            r_squared=1.0, ec30=0.12, doses=[], responses=[],
        )
        tw = compute_therapeutic_window(
            "test", fit, liver_at_ec30=76.0, therapeutic_index=3.0,
            untargeted_ec30=1.54, antibody_required=True,
            has_nhp=False, has_human_exvivo=True,
            manufacturing_complexity="high",
        )
        assert tw.hsc_liver_ratio is not None
        assert abs(tw.hsc_liver_ratio - 30.0 / 76.0) < 0.01

    def test_potency_premium(self) -> None:
        """Potency premium = untargeted / targeted EC30."""
        fit = DoseResponseFit(
            name="test", ec50=0.2, hill=1.5, top=100, bottom=0,
            r_squared=1.0, ec30=0.12, doses=[], responses=[],
        )
        tw = compute_therapeutic_window(
            "test", fit, liver_at_ec30=76.0, therapeutic_index=3.0,
            untargeted_ec30=1.54, antibody_required=True,
            has_nhp=False, has_human_exvivo=True,
            manufacturing_complexity="high",
        )
        assert tw.potency_premium is not None
        assert abs(tw.potency_premium - 1.54 / 0.12) < 1.0

    def test_no_liver_gives_none_ratio(self) -> None:
        """No liver data gives None HSC:liver ratio."""
        tw = compute_therapeutic_window(
            "test", None, liver_at_ec30=None, therapeutic_index=None,
            untargeted_ec30=1.54, antibody_required=True,
            has_nhp=False, has_human_exvivo=False,
            manufacturing_complexity="high",
        )
        assert tw.hsc_liver_ratio is None


# ── Pipeline tests ───────────────────────────────────────────────────────


class TestPipeline:
    """Tests for the analysis pipeline."""

    def test_load_paired_data_without_kim_screen(self) -> None:
        """Loading without Kim screen gives hardcoded points."""
        points = load_paired_data(kim_screen_path=None)
        # 4 Kim E2 + 2 Breda = 6
        assert len(points) == 6
        names = {p.formulation for p in points}
        assert "LNP67" in names
        assert "CD117/LNP" in names

    def test_load_paired_with_kim_screen(self, tmp_path: Path) -> None:
        """Loading with Kim screen adds barcode-paired data."""
        kim_data = {
            "formulations": [
                {
                    "lnp_name": "LNP44",
                    "bm_normalized_bc": 1.0,
                    "liver_ec_normalized_bc": 2.0,
                    "helper_lipid_name": "DOTMA",
                    "peg_chain": "C18",
                },
                {
                    "lnp_name": "LNP85",
                    "bm_normalized_bc": 6.0,
                    "liver_ec_normalized_bc": 2.0,
                    "helper_lipid_name": "DOTAP",
                    "peg_chain": "C14",
                },
                {
                    "lnp_name": "LNP_no_liver",
                    "bm_normalized_bc": 3.0,
                    "liver_ec_normalized_bc": None,
                },
            ],
        }
        kim_path = tmp_path / "kim_screen.json"
        kim_path.write_text(json.dumps(kim_data))

        points = load_paired_data(kim_screen_path=kim_path)
        # 6 hardcoded + 2 from Kim screen (LNP_no_liver excluded)
        assert len(points) == 8
        names = {p.formulation for p in points}
        assert "LNP44" in names
        assert "LNP85" in names
        assert "LNP_no_liver" not in names

    def test_kim_screen_deduplicates_e2(self, tmp_path: Path) -> None:
        """Kim screen skips formulations already in E2 validation."""
        kim_data = {
            "formulations": [
                {
                    "lnp_name": "LNP67",  # duplicate with E2
                    "bm_normalized_bc": 13.0,
                    "liver_ec_normalized_bc": 5.0,
                },
            ],
        }
        kim_path = tmp_path / "kim_screen.json"
        kim_path.write_text(json.dumps(kim_data))

        points = load_paired_data(kim_screen_path=kim_path)
        lnp67_count = sum(1 for p in points if p.formulation == "LNP67")
        assert lnp67_count == 1  # only E2 version

    def test_gap_formulations_count(self) -> None:
        """Five gap formulations identified."""
        gaps = identify_gaps()
        assert len(gaps) == 5
        names = {g.name for g in gaps}
        assert "CD117/2B8 + DOTAP 15% + C18-PEG" in names

    def test_dex_intervention_reduces_ec30(self) -> None:
        """Dex pre-treatment reduces effective EC30."""
        windows = [
            TherapeuticWindow(
                "test", ec30_mg_kg=1.54, liver_at_ec30=25.0,
                hsc_liver_ratio=1.2, therapeutic_index=4.0,
                potency_premium=None, antibody_required=False,
                has_nhp=True, has_human_exvivo=True,
                manufacturing_complexity="low",
            ),
        ]
        effects = model_dex_intervention(windows, bm_boost_factor=1.4)
        assert len(effects) == 1
        assert effects[0].adjusted_ec30 < effects[0].original_ec30

    def test_glycolipid_reduces_liver(self) -> None:
        """Glycolipid substitution reduces liver delivery."""
        windows = [
            TherapeuticWindow(
                "test", ec30_mg_kg=0.12, liver_at_ec30=76.0,
                hsc_liver_ratio=0.39, therapeutic_index=3.0,
                potency_premium=12.0, antibody_required=True,
                has_nhp=False, has_human_exvivo=True,
                manufacturing_complexity="high",
            ),
        ]
        effects = model_glycolipid_intervention(windows, liver_reduction=0.34)
        assert len(effects) == 1
        assert effects[0].adjusted_liver is not None
        assert effects[0].adjusted_liver < effects[0].original_liver  # type: ignore[operator]

    def test_full_analysis_returns_all_sections(self) -> None:
        """Full analysis returns all expected result sections."""
        results = run_full_analysis()
        assert "dose_response_fits" in results
        assert "therapeutic_windows" in results
        assert "pareto" in results
        assert "gap_formulations" in results
        assert "interventions" in results
        assert len(results["dose_response_fits"]) == 4
        assert len(results["therapeutic_windows"]) == 3
        assert len(results["gap_formulations"]) == 5

    def test_full_analysis_saves_files(self, tmp_path: Path) -> None:
        """Full analysis saves JSON output files."""
        run_full_analysis(output_dir=tmp_path)
        assert (tmp_path / "therapeutic_window.json").exists()
        assert (tmp_path / "pareto_frontier.json").exists()

        with (tmp_path / "therapeutic_window.json").open() as f:
            saved = json.load(f)
        assert "dose_response_fits" in saved

    def test_pareto_with_real_data(self) -> None:
        """Pareto frontier computed on hardcoded data has known structure."""
        results = run_full_analysis()
        pareto = results["pareto"]
        assert pareto["n_points"] >= 6
        pareto_names = {
            p["formulation"] for p in pareto["pareto_optimal"]
        }
        assert "CD117/LNP" in pareto_names  # highest BM
        assert "LNP108" in pareto_names      # lowest liver
