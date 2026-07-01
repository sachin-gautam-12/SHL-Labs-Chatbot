import json
import logging
from typing import List, Dict, Any
from app.models.request import Message
from app.models.response import ChatResponse, Recommendation
from app.core.prompt_injection import SecurityGuardrails
from app.core.llm_client import LLMClient
from app.core.retriever import AssessmentRetriever
from app.core.reranker import AssessmentReranker
from app.core.recommender import AssessmentRecommender
from app.core.comparator import AssessmentComparator
from app.core.prompts import (
    SYSTEM_PROMPT_ORCHESTRATOR,
    PROMPT_EXTRACT_REQUIREMENTS,
    PROMPT_CLARIFICATION
)

logger = logging.getLogger(__name__)

class ConversationCoordinator:
    def __init__(self):
        self.guardrails = SecurityGuardrails()
        self.llm_client = LLMClient()
        self.retriever = AssessmentRetriever()
        self.reranker = AssessmentReranker()
        self.recommender = AssessmentRecommender()
        self.comparator = AssessmentComparator()
        logger.info("Initialized ConversationCoordinator successfully")

    def _build_fallback_requirements(self, latest_message: str) -> Dict[str, Any]:
        """Create a deterministic offline requirement map when the LLM is unavailable."""
        message = latest_message.lower()
        job_role = "General role"
        skills = ["problem-solving", "communication"]

        if any(keyword in message for keyword in ["python", "software", "developer", "coding", "programming"]):
            job_role = "Software Developer"
            skills = ["programming", "problem-solving", "software development"]
        elif any(keyword in message for keyword in ["data", "analyst", "analytics"]):
            job_role = "Data Analyst"
            skills = ["data analysis", "statistics", "reporting"]
        elif any(keyword in message for keyword in ["sales", "account executive"]):
            job_role = "Sales Representative"
            skills = ["persuasion", "negotiation", "communication"]
        elif any(keyword in message for keyword in ["customer", "service", "support"]):
            job_role = "Customer Service Representative"
            skills = ["empathy", "communication", "conflict resolution"]
        elif any(keyword in message for keyword in ["manager", "leadership"]):
            job_role = "Manager"
            skills = ["leadership", "decision-making", "team collaboration"]

        return {
            "job_role": job_role,
            "skills": skills,
            "test_type": None,
            "max_duration": None,
            "required_languages": ["English"],
            "requires_adaptive": True,
            "requires_remote": True,
            "intent": "recommend",
            "compare_targets": [],
            "has_sufficient_info": True,
            "fallback_reason": "Used local heuristics because the AI service was unavailable."
        }

    def _build_catalog_fallback(self, search_query: str) -> List[Recommendation]:
        """Build a small set of offline recommendations from the local SHL catalog."""
        matches = []
        lowered_query = search_query.lower()
        for item in self.retriever.catalog[:8]:
            score = 0.0
            if "developer" in lowered_query or "coding" in lowered_query:
                if "coding" in item["name"].lower() or "developer" in item["name"].lower():
                    score = 0.95
                elif "deductive" in item["name"].lower() or "inductive" in item["name"].lower():
                    score = 0.8
            elif "sales" in lowered_query:
                if "sales" in item["name"].lower():
                    score = 0.95
                elif "personality" in item["name"].lower() or "motivation" in item["name"].lower():
                    score = 0.8
            elif "customer" in lowered_query or "service" in lowered_query:
                if "customer service" in item["name"].lower() or "situational" in item["name"].lower():
                    score = 0.95
            else:
                if item["test_type"].lower() in {"cognitive", "behavioral", "technical", "personality"}:
                    score = 0.7

            if score > 0:
                matches.append(
                    Recommendation(
                        name=item["name"],
                        catalog_url=item["url"],
                        test_type=item["test_type"],
                        reason=f"Offline fallback match for your request: {search_query}",
                        confidence_score=round(score, 2),
                        evidence="Selected from the local SHL catalog because the AI service was unavailable."
                    )
                )

        return matches[:3]

    def process_chat(self, messages: List[Message]) -> ChatResponse:
        """Main stateless entry point for processing a conversational step."""
        if not messages:
            return ChatResponse(
                reply="Hello! I am your SHL Assessment Recommender. How can I help you choose the right talent tests today?",
                recommendations=[],
                end_of_conversation=False
            )

        # 1. Inspect the latest message for prompt injection / jailbreaks
        latest_message = messages[-1].content
        is_safe, refusal_reply = self.guardrails.scan_message(latest_message)
        if not is_safe:
            return ChatResponse(
                reply=refusal_reply,
                recommendations=[],
                end_of_conversation=False
            )

        # 2. Format chat history for requirement extraction
        formatted_history = ""
        for msg in messages:
            role_label = "User" if msg.role.lower() == "user" else "Assistant"
            formatted_history += f"{role_label}: {msg.content}\n"

        # Obtain catalog item names for constraint boundary mapping
        catalog_names = [item["name"] for item in self.retriever.catalog]
        catalog_names_str = ", ".join([f"'{name}'" for name in catalog_names])

        # 3. Call LLM to extract requirements, constraints, and current intent
        extraction_prompt = PROMPT_EXTRACT_REQUIREMENTS.format(
            catalog_names=catalog_names_str,
            chat_history=formatted_history
        )

        try:
            extracted = self.llm_client.generate_json(
                prompt=extraction_prompt,
                system_prompt=SYSTEM_PROMPT_ORCHESTRATOR,
                temperature=0.0
            )
            logger.info(f"Extracted state: {extracted}")
        except Exception as exc:
            logger.warning("LLM extraction unavailable; using offline fallback. %s", exc)
            extracted = self._build_fallback_requirements(latest_message)

        intent = extracted.get("intent", "recommend")

        # 4. Handle Off-topic intents flagged by the LLM
        if intent == "off_topic":
            return ChatResponse(
                reply=(
                    "I apologize, but I am only programmed to assist with selecting and "
                    "comparing SHL assessments. Let me know if you would like recommendations "
                    "for specific roles or skills."
                ),
                recommendations=[],
                end_of_conversation=False
            )

        # 5. Handle General Greeting / Idle Chat
        if intent == "general_greeting":
            return ChatResponse(
                reply="Hello! I'm here to recommend the best SHL individual tests for your hiring needs. Tell me about the role and skills you are looking to assess.",
                recommendations=[],
                end_of_conversation=False
            )

        # 6. Handle Comparison Intent
        if intent == "compare":
            compare_targets = extracted.get("compare_targets", [])
            matched_items = []

            # Find catalog items matching requested target names (case-insensitive fuzzy match)
            for target in compare_targets:
                target_clean = target.lower().strip()
                for item in self.retriever.catalog:
                    if target_clean in item["name"].lower() or item["name"].lower() in target_clean:
                        if item not in matched_items:
                            matched_items.append(item)
                            break

            if len(matched_items) >= 2:
                comparison_report = self.comparator.compare_assessments(matched_items)
                return ChatResponse(
                    reply=comparison_report,
                    recommendations=[],
                    end_of_conversation=False
                )
            else:
                return ChatResponse(
                    reply=(
                        "I noticed you wanted to compare assessments, but I couldn't identify "
                        "at least two specific SHL tests from our catalog. Could you please specify "
                        "which tests (e.g. 'OPQ32' and 'Verify Numerical') you'd like to compare?"
                    ),
                    recommendations=[],
                    end_of_conversation=False
                )

        # 7. Handle Recommendation Intent
        has_sufficient_info = extracted.get("has_sufficient_info", False)

        # If requirements are vague, generate clarification question
        if not has_sufficient_info:
            clarify_prompt = PROMPT_CLARIFICATION.format(
                extracted_requirements=json.dumps(extracted)
            )
            clarification_reply = self.llm_client.generate(
                prompt=clarify_prompt,
                system_prompt=SYSTEM_PROMPT_ORCHESTRATOR,
                temperature=0.3
            )
            return ChatResponse(
                reply=clarification_reply,
                recommendations=[],
                end_of_conversation=False
            )

        # Requirements are sufficient. Retrieve and Rerank!
        # Synthesize retrieval search query based on roles and skills
        job_role = extracted.get("job_role") or ""
        skills_str = ", ".join(extracted.get("skills", []))
        search_query = f"Job Role: {job_role}. Skills required: {skills_str}."

        try:
            # Retrieve candidate items
            retrieved_candidates = self.retriever.retrieve(search_query, top_k=7)

            # Compile constraints dictionary for the reranker
            constraints = {
                "max_duration": extracted.get("max_duration"),
                "required_languages": extracted.get("required_languages"),
                "requires_adaptive": extracted.get("requires_adaptive"),
                "requires_remote": extracted.get("requires_remote"),
                "test_type": extracted.get("test_type")
            }

            # Run secondary filtration and reranking
            filtered_candidates = self.reranker.rerank(retrieved_candidates, constraints)
        except Exception as exc:
            logger.warning("Retriever/reranker failed; using catalog fallback. %s", exc)
            filtered_candidates = []

        if not filtered_candidates:
            fallback_recommendations = self._build_catalog_fallback(search_query)
            if fallback_recommendations:
                return ChatResponse(
                    reply=(
                        "The AI service is temporarily unavailable, so I’m returning a few strong SHL catalog matches "
                        "from the local catalog that are relevant to your request."
                    ),
                    recommendations=fallback_recommendations,
                    end_of_conversation=True
                )
            return ChatResponse(
                reply=(
                    "I searched the SHL catalog but couldn't find any assessments that match "
                    "your specific constraints (e.g. duration or language limits). Could you "
                    "please relax the constraints or ask for general role recommendations?"
                ),
                recommendations=[],
                end_of_conversation=False
            )

        if any(keyword in search_query.lower() for keyword in ["coding", "developer", "java", "programming"]):
            coding_item = None
            for item in self.retriever.catalog:
                if "coding assessment" in item["name"].lower():
                    coding_item = item
                    break
            if coding_item:
                existing_names = {item["name"] for item, _ in filtered_candidates}
                if coding_item["name"] not in existing_names:
                    filtered_candidates = [(coding_item, 0.99)] + filtered_candidates
                else:
                    filtered_candidates = [
                        (item, 0.99 if item["name"] == coding_item["name"] else score)
                        for item, score in filtered_candidates
                    ]

        # Generate recommendation cards and justifications
        recommendations = self.recommender.generate_recommendations(
            filtered_candidates,
            extracted
        )

        if not recommendations:
            return ChatResponse(
                reply=(
                    "I found some tests matching your query, but their relevance score was "
                    "too low. Could you tell me more about the role and required skills?"
                ),
                recommendations=[],
                end_of_conversation=False
            )

        # Generate final reply text highlighting recommended tests
        rec_names = [rec.name for rec in recommendations]
        reply_text = (
            f"Based on your requirements for evaluating a **{job_role or 'Candidate'}** role focusing on "
            f"**{skills_str or 'general skills'}**, I recommend the following SHL Individual Test Solutions: "
            f"{', '.join(rec_names)}.\n\n"
            "I have displayed detailed recommendation cards with catalog URLs, test types, and confidence scores below. "
            "Let me know if you would like to compare any of these side-by-side or adjust your criteria!"
        )

        return ChatResponse(
            reply=reply_text,
            recommendations=recommendations,
            end_of_conversation=True
        )
