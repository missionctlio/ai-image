# main.py

from fastapi import FastAPI, HTTPException, Header, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import traceback
import logging
app = FastAPI()

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mount the 'frontend' directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Mount the 'images' directory to serve image files
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")

class PromptRequest(BaseModel):
    prompt: str
    aspectRatio: str  # Added aspect ratio field

class ImageResponse(BaseModel):
    task_id: str  # Task ID for polling status

@app.post("/generate-image")
async def generate_image_endpoint(
    request: Request,
    prompt_request: PromptRequest,
    authorization: str = Header(None),
    api_key: str = Query(None)
):
    try:
        # Determine which method to use for the API key
        api_key = api_key or (authorization.split("Bearer ")[-1] if authorization and "Bearer " in authorization else None)
        
        if not api_key:
            raise HTTPException(status_code=401, detail="API key is required")
        
        # Log or validate the API key if needed
        logger.info(f"Prompt Request: {prompt_request}")
        from backend.celery_config import generate_image_task  # Import Celery task
        # Call the Celery task and get the task ID
        task = generate_image_task.delay(prompt_request.prompt, prompt_request.aspectRatio)
        return {"task_id": task.id}

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    from celery.result import AsyncResult

    try:
        # Check the status of the task
        result = AsyncResult(task_id)
        if result.state == 'PENDING':
            return {"status": 'PENDING'}
        elif result.state == 'SUCCESS':
            return {"status": 'SUCCESS', "result": result.result}
        elif result.state == 'FAILURE':
            return {"status": 'FAILURE', "result": str(result.info)}
        else:
            return {"status": result.state}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Serve the index.html file at the root URL
@app.get("/")
async def read_root():
    return FileResponse('frontend/index.html')
