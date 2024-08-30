from fastapi import HTTPException, Header, Request, APIRouter, Depends
from pydantic import BaseModel
import os
import traceback
import logging
from celery.result import AsyncResult
from app.workers.images import generate_image_task
from app.api.auth import get_current_user  # Import the token verification function
from app.db.database import get_db
from sqlalchemy.orm import Session

logging = logging.getLogger(__name__)

router = APIRouter()

class PromptRequest(BaseModel):
    """
    Request model for generating an image.

    :param userPrompt: The text prompt for image generation.
    :param aspectRatio: The desired aspect ratio of the generated image.
    """
    userPrompt: str
    aspectRatio: str

class ImageResponse(BaseModel):
    """
    Response model for image generation request.

    :param taskId: The task ID used for polling the status of the image generation.
    """
    taskId: str

class DeleteImagesRequest(BaseModel):
    """
    Request model for deleting images.

    :param image_ids: List of image IDs to be deleted.
    """
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
    current_user: dict = Depends(get_current_user)  # Ensure authentication
):
    """
    Endpoint for deleting images based on their IDs.

    :param request: The request body containing a list of image IDs to delete.
    :param authorization: Authorization header containing the Bearer token.
    :param current_user: The current authenticated user.
    :return: A dictionary containing deleted files and any not found files.
    :raises HTTPException: If no image IDs are provided.
    """
    IMAGE_DIR = "frontend/images"
    if not request.image_ids:
        logging.warning("No image IDs provided.")
        raise HTTPException(status_code=400, detail="No image IDs provided")

    deleted_files = []
    not_found_files = []

    logging.info(f"Attempting to delete {len(request.image_ids)} images.")

    for image_id in request.image_ids:
        # Construct file paths with and without 'original_' prefix
        file_paths = [
            os.path.join(IMAGE_DIR, image_id),
            os.path.join(IMAGE_DIR, f"original_{image_id}")
        ]

        # Try deleting files with and without prefix
        deleted = False
        for file_path in file_paths:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    logging.info(f"Deleted file: {file_path}")
                    deleted = True
                    break  # Stop after deleting one version of the file
                except Exception as e:
                    logging.error(f"Failed to delete file: {file_path}. Error: {e}")

        if not deleted:
            not_found_files.append(image_id)
            logging.warning(f"File not found for ID: {image_id}")

    # Response based on the deletion results
    if not_found_files:
        response = {
            "deleted_files": deleted_files,
            "not_found_files": not_found_files,
            "detail": "Some files were not found"
        }
        logging.info("Deletion completed with some files not found.")
    else:
        response = {"deleted_files": deleted_files, "detail": "All specified files deleted successfully"}
        logging.info("All specified files deleted successfully.")

    return response

@router.get("/task-status/{taskId}", response_model=dict)
async def get_task_status(taskId: str, authorization: str = Header(None), current_user: dict = Depends(get_current_user)):
    """
    Endpoint for checking the status of a task.

    :param taskId: The ID of the task to check.
    :param authorization: Authorization header containing the Bearer token.
    :param current_user: The current authenticated user.
    :return: A dictionary containing the status and result of the task.
    :raises HTTPException: If an internal error occurs while checking the task status.
    """
    try:
        # Check the status of the task
        result = AsyncResult(taskId)
        if result.state == 'SUCCESS':
            return {"status": 'SUCCESS', "result": result.result}
        elif result.state == 'FAILURE':
            return {"status": 'FAILURE', "result": str(result.info)}
        else:
            return {"status": result.state}
    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
