import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class AssessmentReranker:
    def __init__(self):
        logger.info("Initialized AssessmentReranker")

    def rerank(
        self, 
        retrieved: List[Tuple[Dict[str, Any], float]], 
        constraints: Dict[str, Any]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Reranks and filters assessments based on structural constraints.
        
        Constraints Dict format:
        {
            "max_duration": Optional[int],
            "required_languages": Optional[List[str]],
            "requires_adaptive": Optional[bool],
            "requires_remote": Optional[bool],
            "test_type": Optional[str]
        }
        """
        if not constraints:
            return retrieved

        reranked = []
        max_duration = constraints.get("max_duration")
        req_languages = constraints.get("required_languages")
        req_adaptive = constraints.get("requires_adaptive")
        req_remote = constraints.get("requires_remote")
        pref_test_type = constraints.get("test_type")

        for item, score in retrieved:
            # 1. Filter by Max Duration
            if max_duration is not None and item.get("duration", 0) > max_duration:
                logger.info(f"Reranker: Filtering out '{item['name']}' - duration {item['duration']} exceeds limit of {max_duration} mins.")
                continue

            # 2. Filter by Remote Support
            if req_remote is True and not item.get("remote_support", True):
                logger.info(f"Reranker: Filtering out '{item['name']}' - does not support remote testing.")
                continue

            # 3. Adjust score based on Adaptive Support matching
            if req_adaptive is not None:
                has_adaptive = item.get("adaptive_support", False)
                if req_adaptive and not has_adaptive:
                    # Penalize score if adaptive is requested but not supported
                    score *= 0.7
                elif not req_adaptive and has_adaptive:
                    # Minor adjustment
                    score *= 0.95

            # 4. Filter by Language Support
            if req_languages:
                item_languages = [lang.lower() for lang in item.get("languages", [])]
                lang_matched = False
                for req_lang in req_languages:
                    if req_lang.lower() in item_languages:
                        lang_matched = True
                        break
                if not lang_matched:
                    logger.info(f"Reranker: Filtering out '{item['name']}' - does not support required languages: {req_languages}.")
                    continue

            # 5. Boost score if test type matches preference
            if pref_test_type and pref_test_type.lower() == item.get("test_type", "").lower():
                score = min(score * 1.15, 1.0)

            # Ensure score is bound between 0 and 1
            score = max(0.0, min(1.0, score))
            reranked.append((item, score))

        # Sort the reranked list by score in descending order
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
