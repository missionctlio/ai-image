from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import torch
from huggingface_hub import login
from app.db.database import get_db, Base, engine
from app.helpers.jwt import create_access_token, verify_token
from app.utils.logging import JSONLoggingMiddleware

load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
if not HF_TOKEN:
    raise ValueError("HUGGINGFACE_TOKEN environment variable is not set.")
torch.cuda.empty_cache()



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "dev.aesync.com"],  # Replace with the origin of your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add the middleware to the application
#app.add_middleware(JSONLoggingMiddleware)


login(token=HF_TOKEN, add_to_git_credential=True)

# JWT Configuration
class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your_secret_key")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Mount the 'frontend' directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")

@app.get("/{filename}")
async def serve_static(filename: str):
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

from app.api.auth import router as auth_router
from app.api.inference.image import router as image_router
from app.api.inference.language import router as language_router
from app.api.users import router as user_router

app.include_router(auth_router, prefix="/auth")
app.include_router(image_router, prefix="/inference/image")
app.include_router(language_router, prefix="/inference/language")
app.include_router(user_router, prefix="/users")

Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_root():
    return FileResponse('frontend/index.html')
