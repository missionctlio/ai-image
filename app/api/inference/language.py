from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request
from pydantic import BaseModel
import logging
import asyncio
import html
import json
from sqlalchemy.orm import Session
from app.db.models import User
from app.db.database import get_db
from collections.abc import Iterator
from app.inference.language.llama.description import generate_description
from app.inference.language.llama.chat import generate_chat
from app.inference.language.llama.refinement import refined_prompt
from app.api.auth import validate_jwt_token, get_current_user
from app.utils.logging import get_logger

# Set up logging configuration
logger = get_logger(__name__)

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

class AuthMessage(BaseModel):
    token: str

# Define the WebSocket endpoint


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    # Accept the WebSocket connection
    await websocket.accept()

    # Extract the query parameters from the WebSocket URL
    query_params = websocket.query_params
    access_token = query_params.get('access_token')

    if not access_token:
        logger.error("Access token missing from query parameters")
        # await websocket.close(code=4000)  # Close with an error code
        return

    # Validate the token and get user info
    try:
        user_info = validate_jwt_token(access_token)
        user_uuid = user_info.get("sub")

        # Fetch user from the database using the user_uuid
        user = get_user_from_uuid(user_uuid, db)
        if not user:
            logger.error("User not found")
            await websocket.close(code=4000)  # Close with an error code
            return

        logger.info(f"User authenticated: {user_info}")

        # Handle chat messages
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received query: {data}")

            chat_response = generate_chat(data)

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