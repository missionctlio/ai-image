from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
import asyncio
import html
from typing import Iterator
from app.db.models import User
from app.db.database import get_db
from app.db.model.user import get_user_from_uuid
from app.api.auth import validate_jwt_token, get_current_user, generate_tokens
from app.inference.language.llama.chat import generate_chat
from app.inference.language.llama.description import generate_description
from app.inference.language.llama.refinement import refined_prompt
from app.utils.conversational_memory import ConversationalMemory  # Import the class

# Set up logging configuration
logger = logging.getLogger(__name__)

router = APIRouter()

class LanguageRequest(BaseModel):
    userPrompt: str


def _escape_html(text: str) -> str:
    """
    Escapes HTML special characters in a given text.

    Args:
        text (str): The text to escape.

    Returns:
        str: The escaped text.
    """
    return html.escape(text)

@router.post("/generate-description")
async def generate_description_endpoint(request: LanguageRequest, current_user: dict = Depends(get_current_user)):
    logger.info("Received request to generate description.")
    logger.info(f"Request payload: {request.dict()}")
    logger.info(f"Current user: {current_user}")
    
    try:
        logger.info("Starting description generation.")
        description = generate_description(request.userPrompt)
        logger.info("Description generated successfully.")
        logger.info(f"Generated description: {description[:100]}...")  # Log first 100 characters for brevity
        return {"description": description}
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        logger.exception("Exception details:")  # Logs traceback with exception details
        raise HTTPException(status_code=500, detail="Error generating description")

@router.post("/generate-refined-prompt")
async def refined_prompt_endpoint(request: LanguageRequest, current_user: dict = Depends(get_current_user)):
    try:
        refinedPrompt = refined_prompt(request.userPrompt)
        return {"refinedPrompt": refinedPrompt}
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating description")

@router.delete("/delete-chat-history")
def delete_chat_history(current_user: dict = Depends(get_current_user)):
    conversation_id = str(current_user.uuid)  # use the user_id (sub) as the conversation_id
    memory = ConversationalMemory(conversation_id)  # Create an instance of ConversationalMemory

    try:
        # Try to clear the conversation memory
        memory.clear_memory()
        return {"status": "success", "message": "Chat history deleted"}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {str(e)}")
        raise HTTPException(status_code=404, detail={"status": "failure", "message": "Chat history not found"})

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    # Accept the WebSocket connection
    await websocket.accept()

    # Extract the query parameters and cookies from the WebSocket
    query_params = websocket.query_params
    access_token = query_params.get('access_token')
    refresh_token = websocket.cookies.get('refresh_token')

    if not access_token and not refresh_token:
        logger.error("Access token and refresh token are missing")
        return

    # Function to validate or refresh access token
    def validate_or_refresh_token():
        nonlocal access_token
        nonlocal refresh_token
        user_info = None
        new_access_token = None

        if access_token:
            try:
                # Validate the access token
                user_info = validate_jwt_token(access_token)
                return user_info, None
            except Exception as e:
                logger.warning(f"Access token validation failed: {e}")

        if refresh_token:
            try:
                # Validate the refresh token
                user_info = validate_jwt_token(refresh_token)
                logger.info(f"Validated refresh token: {user_info}")
                # If refresh token is valid, generate a new access token
                new_access_token, _ = generate_tokens(User(uuid=user_info.get("sub"), email=user_info.get("email"), name=user_info.get("name")))
                logger.info(f"Generated new access token: {new_access_token}")
                access_token = new_access_token
                return user_info, new_access_token
            except Exception as e:
                logger.error(f"Failed to validate refresh token: {e}")

        # If no valid access token or refresh token
        return None, None

    # Ensure the access token is valid or refreshed
    user_info, new_access_token = validate_or_refresh_token()
    if not user_info:
        logger.error("Invalid or expired tokens")
        await websocket.close(code=4000)  # Close with an error code
        return

    # Send the new access token to the client if it was refreshed
    if new_access_token:
        await websocket.send_json({"reauth": True, "new_access_token": new_access_token})

    # Fetch user from the database using the user_uuid
    user_uuid = user_info.get("sub")
    user = get_user_from_uuid(user_uuid, db)
    if not user:
        logger.error("User not found")
        await websocket.close(code=4000)  # Close with an error code
        return

    logger.info(f"User authenticated: {user_info}")

    # Handle chat messages
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received query: {data}")

            chat_response = generate_chat(user_uuid, data)

            if isinstance(chat_response, Iterator):
                for response in chat_response:
                    await websocket.send_text(response)
                    await asyncio.sleep(0.001)
                await websocket.send_text('[END]')
            elif chat_response is not None:
                await websocket.send_text(_escape_html(chat_response))
                await websocket.send_text('[END]')

    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await websocket.send_text("Error: Something went wrong.")
