from pydantic import BaseModel, Field
from typing import List

class Recommendation(BaseModel):
    name: str = Field(
        ..., 
        alias="name", 
        description="The formal name of the recommended SHL assessment."
    )
    catalog_url: str = Field(
        ..., 
        alias="catalog_url", 
        description="The URL leading to the product details page on SHL.com."
    )
    test_type: str = Field(
        ..., 
        alias="test_type", 
        description="The evaluation format, e.g., Cognitive, Personality, Technical."
    )
    reason: str = Field(
        ..., 
        alias="reason", 
        description="A detailed explanation justifying why this assessment fits the job profile."
    )
    confidence_score: float = Field(
        ..., 
        alias="confidence_score", 
        description="Score between 0.0 and 1.0 representing recommendation confidence."
    )
    evidence: str = Field(
        ..., 
        alias="evidence", 
        description="Specific mapping or textual excerpts from the job requirement that triggered this matching."
    )

    class Config:
        populate_by_name = True

class ChatResponse(BaseModel):
    reply: str = Field(
        ..., 
        description="The conversational text response from the assistant."
    )
    recommendations: List[Recommendation] = Field(
        ..., 
        description="A list of 1 to 10 matching assessments. Empty if details are still being gathered."
    )
    end_of_conversation: bool = Field(
        ..., 
        description="Set to true if the final recommendations have been made and the task is complete."
    )
