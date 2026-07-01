import json
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        
        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required for provider 'gemini'")
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model_name = settings.GEMINI_MODEL
            logger.info(f"Initialized LLMClient with Gemini model: {self.model_name}")
            
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for provider 'openai'")
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.model_name = settings.OPENAI_MODEL
                logger.info(f"Initialized LLMClient with OpenAI model: {self.model_name}")
            except ImportError:
                logger.error("Failed to import openai library.")
                raise
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = False
    ) -> str:
        """Generates a text completion from the LLM, supporting text or JSON responses."""
        if self.provider == "gemini":
            return self._generate_gemini(prompt, system_prompt, temperature, json_mode)
        else:
            return self._generate_openai(prompt, system_prompt, temperature, json_mode)

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Generates a structured JSON response from the LLM."""
        response_str = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            json_mode=True
        )
        try:
            # Clean JSON formatting wrappers if returned by the model
            cleaned = response_str.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Failed to parse LLM response as JSON. Raw string: {response_str}. Error: {e}")
            # Return safe fallback dictionary
            return {"error": "Failed to parse JSON response", "raw_content": response_str}

    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = False
    ) -> str:
        import google.generativeai as genai
        
        # Configure model generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json" if json_mode else "text/plain"
        )
        
        # Set up model with optional system instructions
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            generation_config=generation_config
        )
        
        try:
            response = model.generate_content(prompt)
            if not response.text:
                raise RuntimeError("Empty response received from Gemini API.")
            return response.text
        except Exception as e:
            logger.error(f"Gemini API execution failed: {e}")
            raise

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = False
    ) -> str:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response_format = {"type": "json_object"} if json_mode else None
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                response_format=response_format
            )
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("Empty response received from OpenAI API.")
            return content
        except Exception as e:
            logger.error(f"OpenAI API execution failed: {e}")
            raise
