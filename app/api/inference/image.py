from fastapi import HTTPException, Header, Request, APIRouter, Depends
from pydantic import BaseModel
import os
import logging
from celery.result import AsyncResult
from app.workers.images import generate_image_task
from app.api.auth import get_current_user
from typing import Optional
import redis
import traceback
import json

logging = logging.getLogger(__name__)
router = APIRouter()

class PromptRequest(BaseModel):
    userPrompt: str
    aspectRatio: str

class ImageResponse(BaseModel):
    taskId: str

class DeleteImagesRequest(BaseModel):
    image_ids: list[str]

@router.post("/generate-image", response_model=ImageResponse)
async def generate_image_endpoint(
    request: Request,
    prompt_request: PromptRequest,
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)  # Ensure authentication
):
    """
    Endpoint for generating an image based on a prompt and aspect ratio.

    :param request: The HTTP request object.
    :param prompt_request: The request body containing prompt and aspect ratio.
    :param authorization: Authorization header containing the Bearer token.
    :param current_user: The current authenticated user.
    :return: A dictionary containing the task ID for polling status.
    :raises HTTPException: If an internal error occurs.
    """
    try:
        # Log the prompt request
        logging.info(f"Prompt Request: {prompt_request}")

        # Call the Celery task and get the task ID
        task = generate_image_task.delay(prompt_request.userPrompt, prompt_request.aspectRatio)
        return {"taskId": task.id}

    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/delete-images/", response_model=dict)
async def delete_images(
    request: DeleteImagesRequest,
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    IMAGE_DIR = "frontend/images"
    if not request.image_ids:
        logging.warning("No image IDs provided.")
        raise HTTPException(status_code=400, detail="No image IDs provided")

    deleted_files = []
    not_found_files = []
    logging.info(f"Attempting to delete {len(request.image_ids)} images.")

    for image_id in request.image_ids:
        file_paths = [
            os.path.join(IMAGE_DIR, image_id),
            os.path.join(IMAGE_DIR, f"original_{image_id}")
        ]

        deleted = False
        for file_path in file_paths:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    logging.info(f"Deleted file: {file_path}")
                    deleted = True
                    break
                except Exception as e:
                    logging.error(f"Failed to delete file: {file_path}. Error: {e}")

        if not deleted:
            not_found_files.append(image_id)
            logging.warning(f"File not found: {image_id}")

    response = {
        "deleted_files": deleted_files,
        "not_found_files": not_found_files,
        "detail": "Some files were not found" if not_found_files else "All files deleted successfully"
    }
    logging.info("Image deletion completed.")
    return response

@router.get("/task-status/{taskId}", response_model=dict)
async def get_task_status(taskId: str, authorization: str = Header(None), current_user: dict = Depends(get_current_user)):
    try:
        result = AsyncResult(taskId)
        if result.state == 'SUCCESS':
            return {"status": 'SUCCESS', "result": result.result}
        elif result.state == 'FAILURE':
            return {"status": 'FAILURE', "result": str(result.info)}
        return {"status": result.state}
    except Exception as e:
        logging.error(f"Error checking task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task status")

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def get_queued_jobs_from_redis():
    try:
        queued_jobs = r.lrange('celery', 0, -1)
        return len(queued_jobs)
    except Exception as e:
        logging.error(f"Error getting queued jobs: {e}")
        return 0

def get_active_jobs_from_redis():
    try:
        queued_jobs = r.lrange('celery', 0, -1)
        active_jobs_count = sum(
            1 for job in queued_jobs if json.loads(job).get('properties', {}).get('delivery_tag')
        )
        return active_jobs_count
    except Exception as e:
        logging.error(f"Error getting active jobs: {e}")
        return 0

@router.get("/jobs/queued")
async def get_queued_jobs():
    try:
        total_queued_jobs = get_queued_jobs_from_redis()
        total_running_jobs = get_active_jobs_from_redis()
        return {"queued_jobs": total_queued_jobs, "running_jobs": total_running_jobs}
    except Exception as e:
        logging.error(f"Error retrieving job counts: {e}")
        return {"error": "Failed to retrieve job counts"}
