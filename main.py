from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import torch
from huggingface_hub import login
import logging

load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
if not HF_TOKEN:
    raise ValueError("HUGGINGFACE_TOKEN environment variable is not set.")
torch.cuda.empty_cache()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with the origin of your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
login(token=HF_TOKEN, add_to_git_credential=True)
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
    specific_files = {
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "apple-touch-icon.png",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "favicon.ico"
    }
    
    if filename in specific_files:
        file_path = f'frontend/{filename}'
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        raise HTTPException(status_code=404, detail="File not found")

# Include the auth router
from app.backend.api.auth import router as auth_router
app.include_router(auth_router, prefix="/auth")

# Include the API routes
from app.backend.api.api import router as api_router
app.include_router(api_router)

@app.get("/")
async def read_root():
    """
    Endpoint to serve the index.html file at the root URL.

    :return: A FileResponse serving the 'frontend/index.html' file.
    """
    return FileResponse('frontend/index.html')