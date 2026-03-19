"""Tests for multi-objective Pareto optimization."""

from __future__ import annotations

import numpy as np

from lnp_optimizer.pareto import (
    compute_pareto_frontier,
    scalarized_score,
)


class TestParetoFrontier:
    """Tests for Pareto dominance computation."""

    def test_simple_frontier(self) -> None:
        p_bm = np.array([0.9, 0.5, 0.3, 0.8])
        p_liver = np.array([0.3, 0.9, 0.5, 0.8])
        pareto = compute_pareto_frontier(p_bm, p_liver)
        # Point 0 (0.9, 0.3) — not dominated (best BM)
        # Point 1 (0.5, 0.9) — not dominated (best liver)
        # Point 2 (0.3, 0.5) — dominated by point 3
        # Point 3 (0.8, 0.8) — not dominated (best combined)
        assert pareto[0] == True  # noqa: E712
        assert pareto[1] == True  # noqa: E712
        assert pareto[2] == False  # noqa: E712  # dominated
        assert pareto[3] == True  # noqa: E712

    def test_all_pareto(self) -> None:
        p_bm = np.array([0.9, 0.1])
        p_liver = np.array([0.1, 0.9])
        pareto = compute_pareto_frontier(p_bm, p_liver)
        assert pareto.sum() == 2  # tradeoff, both on frontier

    def test_single_dominant(self) -> None:
        p_bm = np.array([0.9, 0.5, 0.3])
        p_liver = np.array([0.9, 0.5, 0.3])
        pareto = compute_pareto_frontier(p_bm, p_liver)
        assert pareto[0] == True  # noqa: E712
        assert pareto[1] == False  # noqa: E712
        assert pareto[2] == False  # noqa: E712

    def test_empty_input(self) -> None:
        p_bm = np.array([])
        p_liver = np.array([])
        pareto = compute_pareto_frontier(p_bm, p_liver)
        assert len(pareto) == 0


class TestScalarizedScore:
    """Tests for weighted scalarized objective."""

    def test_equal_weights(self) -> None:
        p_bm = np.array([0.8, 0.6])
        p_liver = np.array([0.4, 0.8])
        score = scalarized_score(p_bm, p_liver, 0.5, 0.5)
        assert abs(score[0] - 0.6) < 1e-10  # (0.8+0.4)/2
        assert abs(score[1] - 0.7) < 1e-10  # (0.6+0.8)/2

    def test_bm_weighted(self) -> None:
        p_bm = np.array([0.8, 0.2])
        p_liver = np.array([0.2, 0.8])
        score = scalarized_score(p_bm, p_liver, 0.8, 0.2)
        # 0.8*0.8 + 0.2*0.2 = 0.68
        # 0.8*0.2 + 0.2*0.8 = 0.32
        assert score[0] > score[1]

    def test_zero_weights(self) -> None:
        p_bm = np.array([0.8])
        p_liver = np.array([0.5])
        score = scalarized_score(p_bm, p_liver, 1.0, 0.0)
        assert score[0] == 0.8
