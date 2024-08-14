from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Set up logging configuration
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mount the 'frontend' directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Mount the 'images' directory to serve image files
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")

# Include the API routes
from app.backend.api import router as api_router
app.include_router(api_router)

@app.get("/")
async def read_root():
    """
    Endpoint to serve the index.html file at the root URL.

    :return: A FileResponse serving the 'frontend/index.html' file.
    """
    return FileResponse('frontend/index.html')
