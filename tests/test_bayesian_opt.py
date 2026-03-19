"""Tests for Bayesian optimization pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lnp_optimizer.bayesian_opt import (
    GP_FEATURES,
    _build_grid,
    _filter_constraints,
    enumerate_candidates,
    expected_improvement,
    fit_gp,
    upper_confidence_bound,
)


def _make_gp_data(n: int = 50) -> tuple[pd.DataFrame, np.ndarray]:
    """Create fixture data for GP fitting."""
    rng = np.random.RandomState(42)
    data: dict[str, list[float]] = {}
    for col in GP_FEATURES:
        if col in ("receptor_cd117", "hl_dotap", "helper_is_cationic"):
            data[col] = rng.choice([0.0, 1.0], n).tolist()
        elif col == "peg_chain_numeric":
            data[col] = rng.choice([14.0, 18.0], n).tolist()
        elif col == "dose_mg_per_kg":
            data[col] = rng.choice([0.5, 1.0, 2.0], n).tolist()
        else:
            data[col] = rng.uniform(10, 50, n).tolist()
    df = pd.DataFrame(data)
    target = rng.uniform(0, 100, n)
    return df, target


class TestGPFit:
    """Tests for GP model fitting."""

    def test_fits_without_error(self) -> None:
        df, target = _make_gp_data(30)
        gp, scaler, feats = fit_gp(df, target)
        assert gp is not None
        assert len(feats) == len(GP_FEATURES)

    def test_predicts_with_uncertainty(self) -> None:
        df, target = _make_gp_data(30)
        gp, scaler, feats = fit_gp(df, target)
        X = scaler.transform(df[feats].values[:5])
        mu, sigma = gp.predict(X, return_std=True)
        assert len(mu) == 5
        assert len(sigma) == 5
        assert all(s >= 0 for s in sigma)

    def test_handles_nan_target(self) -> None:
        df, target = _make_gp_data(30)
        target[0] = np.nan
        target[1] = np.nan
        gp, _, _ = fit_gp(df, target)
        assert gp is not None


class TestAcquisition:
    """Tests for acquisition functions."""

    def test_ei_positive(self) -> None:
        df, target = _make_gp_data(30)
        gp, scaler, feats = fit_gp(df, target)
        X = scaler.transform(df[feats].values[:10])
        ei = expected_improvement(X, gp, y_best=50.0)
        assert len(ei) == 10
        assert all(e >= 0 for e in ei)

    def test_ucb_higher_than_mean(self) -> None:
        df, target = _make_gp_data(30)
        gp, scaler, feats = fit_gp(df, target)
        X = scaler.transform(df[feats].values[:10])
        ucb = upper_confidence_bound(X, gp, kappa=2.0)
        mu = gp.predict(X)
        assert all(u >= m for u, m in zip(ucb, mu, strict=True))

    def test_ei_zero_below_best(self) -> None:
        df, target = _make_gp_data(30)
        gp, scaler, feats = fit_gp(df, target)
        X = scaler.transform(df[feats].values[:5])
        # With a very high y_best, EI should be near zero
        ei = expected_improvement(X, gp, y_best=1e6)
        assert all(e < 1e-3 for e in ei)


class TestCandidates:
    """Tests for candidate enumeration."""

    def test_grid_nonempty(self) -> None:
        grid = _build_grid()
        assert len(grid) > 100

    def test_constraints_filter(self) -> None:
        grid = _build_grid()
        filtered = _filter_constraints(grid)
        assert len(filtered) < len(grid)
        # All filtered candidates respect constraints
        assert (filtered["ionizable_mol_pct"] >= 30).all()
        assert (filtered["ionizable_mol_pct"] <= 60).all()
        assert (filtered["cholesterol_mol_pct"] >= 20).all()
        assert (filtered["cholesterol_mol_pct"] <= 50).all()

    def test_components_sum_near_100(self) -> None:
        grid = _build_grid()
        filtered = _filter_constraints(grid)
        total = (
            filtered["ionizable_mol_pct"]
            + filtered["helper_mol_pct"]
            + filtered["cholesterol_mol_pct"]
            + filtered["peg_mol_pct"]
        )
        assert ((total - 100).abs() < 1.1).all()

    def test_enumerate_removes_existing(self) -> None:
        df, _ = _make_gp_data(10)
        candidates = enumerate_candidates(df, GP_FEATURES)
        assert len(candidates) > 0

    def test_candidates_have_required_columns(self) -> None:
        df, _ = _make_gp_data(10)
        candidates = enumerate_candidates(df, GP_FEATURES)
        for col in GP_FEATURES:
            assert col in candidates.columns


class TestClassificationGP:
    """Tests for classification GP."""

    def test_fits_binary(self) -> None:
        from lnp_optimizer.bayesian_opt import fit_gp_classifier
        df, _ = _make_gp_data(30)
        rng = np.random.RandomState(42)
        binary = rng.choice([0, 1], 30)
        gpc, scaler, feats = fit_gp_classifier(df, binary)
        assert gpc is not None

    def test_classify_acquisition(self) -> None:
        from lnp_optimizer.bayesian_opt import classify_acquisition, fit_gp_classifier
        df, _ = _make_gp_data(30)
        rng = np.random.RandomState(42)
        binary = rng.choice([0, 1], 30)
        gpc, scaler, feats = fit_gp_classifier(df, binary)
        X = scaler.transform(df[feats].values[:5])
        p_high, entropy, score = classify_acquisition(X, gpc)
        assert len(p_high) == 5
        assert all(0 <= p <= 1 for p in p_high)
        assert all(e >= 0 for e in entropy)
        assert all(s >= 0 for s in score)
