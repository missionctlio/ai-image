from fastapi import FastAPI, HTTPException, Header, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.diffusion import generate_image
from backend.prompt_refiner import generate_description
import traceback

app = FastAPI()

# Mount the 'frontend' directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Mount the 'images' directory to serve image files
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")

class PromptRequest(BaseModel):
    prompt: str
    aspectRatio: str  # Added aspect ratio field

class ImageResponse(BaseModel):
    image_url: str  # URL to the generated image
    description: str  # Generated description

@app.post("/generate-image", response_model=ImageResponse)
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
        print(f"API Key received: {api_key}")
        print(f"User Prompt: {prompt_request.prompt}")
        print(f"Aspect Ratio: {prompt_request.aspectRatio}")

        # Generate the image with the provided aspect ratio
        image_id = generate_image(prompt_request.prompt, prompt_request.aspectRatio)
        image_url = f"/images/{image_id}.png"
        
        # Generate the description
        description = generate_description(prompt_request.prompt)
        
        return ImageResponse(image_url=image_url, description=description)

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Serve the index.html file at the root URL
@app.get("/")
async def read_root():
    return FileResponse('frontend/index.html')
