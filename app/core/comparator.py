import logging
import json
from typing import List, Dict, Any
from app.core.llm_client import LLMClient
from app.core.prompts import PROMPT_COMPARATOR

logger = logging.getLogger(__name__)

class AssessmentComparator:
    def __init__(self):
        self.llm_client = LLMClient()
        logger.info("Initialized AssessmentComparator")

    def compare_assessments(self, assessments: List[Dict[str, Any]]) -> str:
        """Generates a structured comparison matrix and text analysis for a list of assessments."""
        if not assessments:
            return "No assessments were provided for comparison."

        if len(assessments) < 2:
            return "Please select at least two assessments to compare."

        # 1. Programmatically construct the Markdown Comparison Matrix to guarantee accuracy
        matrix_header = (
            "\n### Side-by-Side Comparison Matrix\n\n"
            "| Feature | " + " | ".join([item["name"] for item in assessments]) + " |\n"
            "| :--- | " + " | ".join([":---:" for _ in assessments]) + " |\n"
        )
        
        # Row definitions
        rows = [
            ("Category", lambda x: x.get("category", "N/A")),
            ("Test Type", lambda x: x.get("test_type", "N/A")),
            ("Duration", lambda x: f"{x.get('duration', 0)} mins"),
            ("Adaptive (IRT) Support", lambda x: "Yes" if x.get("adaptive_support") else "No"),
            ("Remote Testing Support", lambda x: "Yes" if x.get("remote_support") else "No"),
            ("Languages Supported", lambda x: ", ".join(x.get("languages", []))),
            ("Skills Measured", lambda x: ", ".join(x.get("skills", []))),
        ]

        matrix_rows = []
        for label, extractor in rows:
            row_str = f"| **{label}** | " + " | ".join([extractor(item) for item in assessments]) + " |"
            matrix_rows.append(row_str)
            
        markdown_table = matrix_header + "\n".join(matrix_rows) + "\n\n"

        # 2. Use LLM to write qualitative comparison (Purpose, Strengths, Weaknesses/Limitations)
        assessments_data_str = json.dumps(assessments, indent=2)
        prompt = PROMPT_COMPARATOR.format(assessments_data=assessments_data_str)
        
        try:
            comparison_analysis = self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are an expert psychometrician comparing SHL products.",
                temperature=0.2
            )
        except Exception as e:
            logger.error(f"Error calling LLM for comparison: {e}")
            comparison_analysis = (
                "**Assessment Highlights:**\n" + 
                "\n".join([f"- **{item['name']}**: Focuses on {', '.join(item['skills'])}. Best suited for {', '.join(item['job_roles'])}." for item in assessments])
            )

        # Merge table and qualitative analysis
        full_report = (
            "Here is the side-by-side comparison you requested:\n"
            f"{markdown_table}"
            "### Comparative Analysis\n\n"
            f"{comparison_analysis}"
        )
        
        return full_report
