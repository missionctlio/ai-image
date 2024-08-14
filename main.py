from fastapi import FastAPI,HTTPException
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
# Custom route to serve specific files directly from the root
@app.get("/{filename}")
async def serve_static(filename: str):
    """
    Endpoint to serve specific files from the root URL.

    :param filename: The name of the file to serve.
    :return: A FileResponse serving the requested file.
    """
    # List of specific files to be served from the root
    specific_files = {
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "apple-touch-icon.png",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "favicon.ico"
    }
    
    # Check if the requested file is in the list of specific files
    if filename in specific_files:
        file_path = f'frontend/{filename}'
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        raise HTTPException(status_code=404, detail="File not found")

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
