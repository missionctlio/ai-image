from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.diffusion import generate_image
import traceback

app = FastAPI()

# Mount the 'frontend' directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Replace with your actual API key
API_KEY = "your-secret-api-key"

class PromptRequest(BaseModel):
    prompt: str

class ImageResponse(BaseModel):
    image: str  # Single base64 encoded image data

# Middleware to check API key
@app.middleware("http")
async def check_api_key(request: Request, call_next):
    api_key = request.query_params.get("api_key")
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    response = await call_next(request)
    return response

@app.post("/generate-image", response_model=ImageResponse)
async def generate_image_endpoint(request: PromptRequest):
    try:
        # Generate the image
        image = generate_image(request.prompt)
        return ImageResponse(image=image)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Serve the index.html file at the root URL
@app.get("/")
async def read_root():
    return FileResponse('frontend/index.html')
