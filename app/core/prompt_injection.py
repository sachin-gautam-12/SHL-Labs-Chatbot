import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class SecurityGuardrails:
    def __init__(self):
        # Heuristics for common jailbreak patterns, prompt leakage, and developer overrides
        self.injection_patterns = [
            r"ignore\s+(?:the\s+)?previous\s+instructions",
            r"ignore\s+all\s+(?:previous\s+)?directions",
            r"ignore\s+rules",
            r"what\s+are\s+your\s+instructions",
            r"reveal\s+(?:your\s+)?system\s+(?:prompt|instruction)",
            r"reveal\s+hidden\s+prompt",
            r"system\s+prompt\s+leak",
            r"you\s+are\s+now\s+in\s+developer\s+mode",
            r"developer\s+mode\s+active",
            r"bypass\s+(?:safety|rules|constraints)",
            r"do\s+anything\s+now",
            r"\b\(?dan\)?\b",  # Do Anything Now jailbreak reference
            r"jailbreak",
            r"write\s+a\s+python\s+script\s+to\b", # general code writing bypass
            r"translate\s+the\s+system\s+instruction"
        ]

        # Heuristics for off-topic areas (legal advice, broad non-SHL hiring queries)
        self.off_topic_patterns = [
            r"\bis\s+it\s+legal\s+to\b",
            r"\blegal\s+liability\b",
            r"\blegality\s+of\b",
            r"\bsue\b",
            r"\blawsuit\b",
            r"\bsalary\s+negotiation\b",
            r"\bsalary\s+range\b",
            r"\bhow\s+much\s+should\s+i\s+pay\b",
            r"\bhow\s+much\s+should\s+i\s+offer\b",
            r"\bjob\s+offer\s+template\b",
            r"\bbackground\s+check\b",
            r"\bbackground\s+check\s+service\b"
        ]

        # Compile regexes
        self.injection_regex = re.compile("|".join(self.injection_patterns), re.IGNORECASE)
        self.off_topic_regex = re.compile("|".join(self.off_topic_patterns), re.IGNORECASE)

    def scan_message(self, content: str) -> Tuple[bool, str]:
        """Scans user message for security violations or off-topic prompts.

        Returns (is_safe, refusal_message).
        """
        # 1. Check for prompt injection / jailbreak attempts
        if self.injection_regex.search(content):
            logger.warning("Prompt injection attempt intercepted via heuristic scanner.")
            return False, (
                "Security Alert: Request denied. I am a specialized SHL Assessment Recommender. "
                "I cannot bypass my system instructions, reveal developer prompts, or execute "
                "unrelated programming tasks."
            )

        # 2. Check for legal advice or out-of-scope hiring assistance
        if self.off_topic_regex.search(content):
            logger.warning("Off-topic inquiry (legal/hiring) intercepted via heuristic scanner.")
            return False, (
                "Policy Notice: I can only recommend and compare SHL assessment solutions. "
                "For legal advice regarding employment screening or general hiring policies, "
                "please consult your organization's legal and human resources counsel."
            )

        return True, ""
