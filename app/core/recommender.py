import logging
import json
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.core.llm_client import LLMClient
from app.core.prompts import PROMPT_RECOMMENDER_EXPLAIN
from app.models.response import Recommendation

logger = logging.getLogger(__name__)

class AssessmentRecommender:
    def __init__(self):
        self.llm_client = LLMClient()
        self.threshold = settings.CONFIDENCE_THRESHOLD
        logger.info(f"Initialized AssessmentRecommender with threshold: {self.threshold}")

    def generate_recommendations(
        self,
        retrieved_items: List[Tuple[Dict[str, Any], float]],
        requirements: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generates structured Recommendation models for the top matched assessments."""
        recommendations = []

        # Limit processing to a maximum of 10 items to prevent context bloat and cost
        candidate_items = retrieved_items[:10]

        for item, retriever_score in candidate_items:
            logger.info(f"Scoring candidate assessment: {item['name']} (Retriever similarity: {retriever_score:.2f})")

            # Format requirements and assessment data for the LLM scoring template
            user_req_str = json.dumps(requirements, indent=2)
            item_details_str = json.dumps(item, indent=2)

            prompt = PROMPT_RECOMMENDER_EXPLAIN.format(
                user_requirements=user_req_str,
                assessment_details=item_details_str
            )

            try:
                # Query LLM to justify the recommendation and provide scores
                llm_response = self.llm_client.generate_json(
                    prompt=prompt,
                    system_prompt="You are a precise SHL grading agent.",
                    temperature=0.0
                )

                # Use the LLM-provided score when available so the recommendation stays aligned with the model's reasoning.
                llm_score = float(llm_response.get("confidence_score", retriever_score))
                final_confidence = llm_score

                # Filter out low confidence matches
                if final_confidence < self.threshold:
                    logger.info(f"Discarded '{item['name']}' - final confidence {final_confidence:.2f} below threshold {self.threshold}")
                    continue

                rec = Recommendation(
                    name=item["name"],
                    catalog_url=item["url"],
                    test_type=item["test_type"],
                    reason=llm_response.get("reason", f"Highly recommended assessment measuring target competencies for {requirements.get('job_role', 'this role')}."),
                    confidence_score=round(final_confidence, 2),
                    evidence=llm_response.get("evidence", "Semantic match with skills and requirements.")
                )
                recommendations.append(rec)

            except Exception as e:
                logger.error(f"Error compiling recommendation for {item['name']}: {e}")
                # Fallback to direct heuristic recommendations if LLM fails
                if retriever_score >= self.threshold:
                    rec = Recommendation(
                        name=item["name"],
                        catalog_url=item["url"],
                        test_type=item["test_type"],
                        reason=f"Recommended cognitive/technical screening based on matching skills: {', '.join(item.get('skills', []))}.",
                        confidence_score=round(retriever_score, 2),
                        evidence="Automatic heuristic fallback match."
                    )
                    recommendations.append(rec)

        # Sort recommendations by confidence score descending
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)

        # Enforce the 1 to 10 limit
        final_recommendations = recommendations[:10]
        logger.info(f"Compiled {len(final_recommendations)} qualified recommendations.")

        return final_recommendations
