from main import app
from fastapi import HTTPException, Header, Request, Query, APIRouter
from pydantic import BaseModel
import os
import traceback
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

class PromptRequest(BaseModel):
    """
    Request model for generating an image.

    :param prompt: The text prompt for image generation.
    :param aspectRatio: The desired aspect ratio of the generated image.
    :param usePromptRefiner: Boolean indicating whether to use prompt refinement.
    """
    prompt: str
    aspectRatio: str
    usePromptRefiner: bool

class ImageResponse(BaseModel):
    """
    Response model for image generation request.

    :param task_id: The task ID used for polling the status of the image generation.
    """
    task_id: str

class DeleteImagesRequest(BaseModel):
    """
    Request model for deleting images.

    :param image_ids: List of image IDs to be deleted.
    """
    image_ids: list[str]


@app.post("/generate-image")
async def generate_image_endpoint(
    request: Request,
    prompt_request: PromptRequest,
    authorization: str = Header(None),
    api_key: str = Query(None)
):
    """
    Endpoint for generating an image based on a prompt and aspect ratio.

    :param request: The HTTP request object.
    :param prompt_request: The request body containing prompt and aspect ratio.
    :param authorization: Optional authorization header for API key.
    :param api_key: Optional query parameter for API key.
    :return: A dictionary containing the task ID for polling status.
    :raises HTTPException: If API key is missing or an internal error occurs.
    """
    try:
        # Determine which method to use for the API key
        api_key = api_key or (authorization.split("Bearer ")[-1] if authorization and "Bearer " in authorization else None)
        
        if not api_key:
            raise HTTPException(status_code=401, detail="API key is required")
        
        # Log or validate the API key if needed
        logger.info(f"Prompt Request: {prompt_request}")
        from app.workers.images import generate_image_task  # Import Celery task
        # Call the Celery task and get the task ID
        task = generate_image_task.delay(prompt_request.prompt, prompt_request.aspectRatio, prompt_request.usePromptRefiner)
        return {"task_id": task.id}

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete-images/")
async def delete_images(request: DeleteImagesRequest):
    """
    Endpoint for deleting images based on their IDs.

    :param request: The request body containing a list of image IDs to delete.
    :return: A dictionary containing deleted files and any not found files.
    :raises HTTPException: If no image IDs are provided.
    """
    IMAGE_DIR = "frontend/images"
    if not request.image_ids:
        logger.warning("No image IDs provided.")
        raise HTTPException(status_code=400, detail="No image IDs provided")

    deleted_files = []
    not_found_files = []

    logger.info(f"Attempting to delete {len(request.image_ids)} images.")

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
                    logger.info(f"Deleted file: {file_path}")
                    deleted = True
                    break  # Stop after deleting one version of the file
                except Exception as e:
                    logger.error(f"Failed to delete file: {file_path}. Error: {e}")

        if not deleted:
            not_found_files.append(image_id)
            logger.warning(f"File not found for ID: {image_id}")

    # Response based on the deletion results
    if not_found_files:
        response = {
            "deleted_files": deleted_files,
            "not_found_files": not_found_files,
            "detail": "Some files were not found"
        }
        logger.info("Deletion completed with some files not found.")
    else:
        response = {"deleted_files": deleted_files, "detail": "All specified files deleted successfully"}
        logger.info("All specified files deleted successfully.")

    return response

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Endpoint for checking the status of a task.

    :param task_id: The ID of the task to check.
    :return: A dictionary containing the status and result of the task.
    :raises HTTPException: If an internal error occurs while checking the task status.
    """
    from celery.result import AsyncResult

    try:
        # Check the status of the task
        result = AsyncResult(task_id)
        if result.state == 'SUCCESS':
            return {"status": 'SUCCESS', "result": result.result}
        elif result.state == 'FAILURE':
            return {"status": 'FAILURE', "result": str(result.info)}
        else:
            return {"status": result.state}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
