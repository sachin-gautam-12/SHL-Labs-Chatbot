import logging
from fastapi import APIRouter, HTTPException, Depends
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.core.conversation import ConversationCoordinator

logger = logging.getLogger(__name__)

router = APIRouter()

# Instantiate the stateless coordinator.
# In a larger application, this would be injected using Depends.
coordinator = ConversationCoordinator()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Stateless chat endpoint that processes messages and returns recommendations or comparisons."""
    logger.info(f"Received chat request with {len(request.messages)} messages")
    try:
        response = coordinator.process_chat(request.messages)
        return response
    except Exception as e:
        logger.exception("Error processing chat request: %s", e)
        return ChatResponse(
            reply=(
                "I couldn't complete that request because the AI service or SHL catalog was temporarily unavailable. "
                "Please try again with a more specific role and skill description."
            ),
            recommendations=[],
            end_of_conversation=False
        )
