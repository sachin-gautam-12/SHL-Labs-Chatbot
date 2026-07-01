from pydantic import BaseModel, Field
from typing import List

class Message(BaseModel):
    role: str = Field(
        ..., 
        description="The role of the message sender, typically 'user', 'assistant', or 'system'."
    )
    content: str = Field(
        ..., 
        description="The textual content of the message."
    )

class ChatRequest(BaseModel):
    messages: List[Message] = Field(
        ..., 
        description="The chronological list of messages in the current conversation session."
    )
