from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
import asyncio
import html
from typing import Iterator
from app.db.models import User
from app.db.database import get_db
from app.api.auth import validate_jwt_token, get_current_user
from app.inference.language.llama.chat import generate_chat
from app.inference.language.llama.description import generate_description
from app.inference.language.llama.refinement import refined_prompt

# Set up logging configuration
logger = logging.getLogger(__name__)

router = APIRouter()

class LanguageRequest(BaseModel):
    userPrompt: str

@router.post("/generate-description")
async def generate_description_endpoint(request: LanguageRequest, current_user: dict = Depends(get_current_user)):
    try:
        description = generate_description(request.userPrompt)
        return {"description": description}
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating description")

@router.post("/generate-refined-prompt")
async def refined_prompt_endpoint(request: LanguageRequest, current_user: dict = Depends(get_current_user)):
    try:
        refinedPrompt = refined_prompt(request.userPrompt)
        return {"refinedPrompt": refinedPrompt}
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating description")

def _escape_html(text: str) -> str:
    return html.escape(text)


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
        #await websocket.close(code=4000)  # Close with an error code
        return

    # Function to validate or refresh access token
    def validate_or_refresh_token():
        nonlocal access_token
        nonlocal refresh_token
        if access_token:
            try:
                # Validate the access token
                user_info = validate_jwt_token(access_token)
                return user_info
            except Exception as e:
                logger.warning(f"Access token validation failed: {e}")

        if refresh_token:
            try:
                # Validate the refresh token
                user_info = validate_jwt_token(access_token)
                # If refresh token is valid, consider it as authenticated
                # Note: If you need a new access token, you would handle that separately
                return user_info

            except Exception as e:
                logger.error(f"Failed to validate refresh token: {e}")

        # If no valid access token or refresh token
        return None

    # Ensure the access token is valid or refreshed
    user_info = validate_or_refresh_token()
    if not user_info:
        logger.error("Invalid or expired tokens")
        #await websocket.close(code=4000)  # Close with an error code
        return

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

            chat_response = generate_chat(user_uuid,data)

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

def get_user_from_uuid(user_uuid: str, db: Session) -> User:
    """Fetch user from the database by UUID."""
    return db.query(User).filter(User.uuid == user_uuid).first()
def _escape_html(text: str) -> str:
    """
    Escapes HTML special characters in a given text.

    Args:
        text (str): The text to escape.

    Returns:
        str: The escaped text.
    """
    return html.escape(text)