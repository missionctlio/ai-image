from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
import logging
import asyncio
import html
from collections.abc import Iterator
from app.inference.language.llama.description import generate_description
from app.inference.language.llama.chat import generate_chat
from app.inference.language.llama.refinement import refined_prompt
from app.api.auth import validate_jwt_token, get_current_user


router = APIRouter()

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Receive the first message containing the auth token
        auth_message = await websocket.receive_text()
        auth_data = AuthMessage.parse_raw(auth_message)
        token = auth_data.token

        # Validate the token
        try:
            user_info = validate_jwt_token(token)
            logger.info(f"User authenticated: {user_info}")
        except HTTPException as e:
            logger.error(f"Authentication failed: {e.detail}")
            await websocket.close(code=4000)  # Close with an error code
            return
        
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