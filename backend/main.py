from fastapi import FastAPI, HTTPException, Header, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.diffusion import generate_image
import traceback

app = FastAPI()

# Mount the 'frontend' directory to serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Mount the 'images' directory to serve image files
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")

class PromptRequest(BaseModel):
    prompt: str
class ImageResponse(BaseModel):
    image_url: str  # URL to the generated image


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

         # Generate the image
        image_id = generate_image(prompt_request.prompt)
        image_url = f"/images/{image_id}.png"
        
        return ImageResponse(image_url=image_url)

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Serve the index.html file at the root URL
@app.get("/")
async def read_root():
    return FileResponse('frontend/index.html')
