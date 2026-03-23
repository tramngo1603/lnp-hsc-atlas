"""Formulation recommendation engine.

Given a target tissue, payload type, and efficiency threshold, returns
ranked candidate formulations with predicted efficiency, confidence
intervals, and supporting literature citations.
"""

from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    """Input parameters for a formulation recommendation."""

    target_tissue: str
    payload_type: str
    efficiency_threshold: float = 0.0


class RecommendationResult(BaseModel):
    """A single recommended formulation with supporting evidence."""

    formulation_id: int
    predicted_efficiency: float
    confidence_lower: float
    confidence_upper: float
    supporting_pmids: list[str]
    explanation: str


class FormulationRecommender:
    """Recommend optimal LNP formulations for a given target and payload."""

    async def recommend(
        self, request: RecommendationRequest, top_k: int = 10
    ) -> list[RecommendationResult]:
        """Generate ranked formulation recommendations.

        Args:
            request: Target tissue, payload type, and threshold.
            top_k: Maximum number of recommendations to return.

        Returns:
            List of RecommendationResult, sorted by predicted efficiency.
        """
        raise NotImplementedError
