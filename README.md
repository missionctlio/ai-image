# Image Generation App

## Overview

This application allows users to generate and upscale images based on text prompts. It integrates with an image generation API, provides theme switching functionality, and uses Real-ESRGAN for image upscaling. Users can view results with detailed descriptions and manage generated images.

### Screenshots

<div style="display: flex; justify-content: space-between; gap: 10px;">
<div style="display: flex; justify-content: space-between; gap: 10px;">
    <img src="https://github.com/user-attachments/assets/064189f0-7030-429b-9d04-3243e4dfdd45" alt="Image 1" style="width: 48%; height: auto; object-fit: cover;">
    <img src="https://github.com/user-attachments/assets/05b8197b-4291-49ac-a086-da7fa01af827" alt="Image 2" style="width: 48%; height: auto; object-fit: cover;">
    <img src="https://github.com/user-attachments/assets/176476c9-c5ea-4a74-a082-bd8e8df84c6f" alt="Image 3" style="width: 48%; height: auto; object-fit: cover;">
    <img src="https://github.com/user-attachments/assets/09519c44-bf62-4dac-a32f-f2c9869a13ca" alt="Image 4" style="width: 48%; height: auto; object-fit: cover;">
</div>

</div>

## Features

- **Image Generation**: Submit prompts to generate images via the `/generate-image` API endpoint.
- **Image Upscaling**: Enhance image quality using Real-ESRGAN for upscaling.
- **Prompt Handling**: Displays both the original and refined prompts combined with a line break.
- **Theme Switcher**: Toggle between light and dark themes for a personalized user experience.
- **Image Display**: View full-size images with associated details.
- **Image Management**: Save generated images to local storage, view thumbnails, and delete images.
- **Thumbnails**: Automatically load and display thumbnails of saved images.
- **Polling**: Continuously check the status of image generation tasks with retries.
- **Error Handling**: Provides feedback on errors and issues during the image generation and management process.
- **Meta-Llama LLaMA3 Integration**: Uses Meta-Llama LLaMA3 for language-based prompt refinement and description generation.
- **Black-Forest-Labs Flux Diffuser Integration**: Utilizes Black-Forest-Labs Flux Diffuser for the image diffusion process.

## Technologies Used

- **Frontend**:
  - HTML
  - CSS
  - JavaScript

- **Backend**:
  - FastAPI
  - Celery
  - Redis

- **Inference**:
  - **Meta-Llama LLaMA3**: Used for language-based prompt refinement and description generation.
  - **Black-Forest-Labs Flux Diffuser**: Utilized for the image diffusion process.
  - **Real-ESRGAN**: Enhances image quality through upscaling.

- **Database**:
  - Local Storage (for saving images and metadata)

## API Endpoints

### POST /generate-image

Generates an image based on the provided prompt and aspect ratio.

**Request Body:**

```json
{
    "prompt": "string",
    "aspectRatio": "string"
}
```

**Response:**

```json
{
    "task_id": "string"
}
```

### GET /task-status/{taskId}

Checks the status of the image generation task.

**URL Parameters:**
- `taskId`: The ID of the task to check.

**Response:**

```json
{
    "status": "string",
    "result": {
        "image_url": "string",
        "description": "string",
        "refined_prompt": "string"
    }
}
```

### POST /upscale-image

Upscales an image using Real-ESRGAN.

**Request Body:**

```json
{
    "image_url": "string"
}
```

**Response:**

```json
{
    "upscaled_image_url": "string"
}
```

### DELETE /delete-images/

Deletes images from the server.

**Request Body:**

```json
{
    "image_ids": ["string"]
}
```

**Response:**

```json
{
    "status": "string"
}
```

## Application Structure

The application is organized into several components, each serving a specific purpose:

- **Frontend**:
  - `frontend/index.html`: Main HTML file for the user interface.
  - `frontend/style.css`: CSS styles for the application.
  - `frontend/app.js`: JavaScript handling UI interactions and API calls.
  - `frontend/images/`: Directory for storing image assets.

- **Backend**:
  - `app/backend/api.py`: FastAPI application entry point.

- **Inference**:
  - **Image**:
    - **Flux Diffuser**:
      - `app/inference/image/flux/diffuser.py`: Image diffusion logic using the Black-Forest-Labs Flux Diffuser.
      - `app/inference/image/flux/model.py`: Model-related logic for the Flux Diffuser.
    - **Real-ESRGAN**:
      - `app/inference/image/realesrgan/model.py`: Model-related logic for Real-ESRGAN.
      - `app/inference/image/realesrgan/rescaler.py`: Image upscaling logic using Real-ESRGAN.
  - **Language**:
    - **Llama**:
      - `app/inference/language/llama/description.py`: Description generation using Meta-Llama LLaMA3.
      - `app/inference/language/llama/model.py`: Language model logic using Meta-Llama LLaMA3.
      - `app/inference/language/llama/refinement.py`: Prompt refinement using Meta-Llama LLaMA3.

- **Workers**:
  - `app/workers/celery_config.py`: Celery configuration for workers.
  - `app/workers/images.py`: Image processing tasks.

- **Docker**:
  - `docker-compose.yaml`: Defines the services for Docker Compose.

- **Startup**:
  - `run.sh`: Script to build and run Docker containers.

- **Main**:
  - `main.py`: Entry point for running the FastAPI application.

- **Dependencies**:
  - `requirements.txt`: Lists the Python dependencies for the project.

## Setup and Installation

### Prerequisites

- Docker
- Docker Compose
- Python 3.x

### Running the Application

1. **Clone the Repository**

   ```
   git clone https://github.com/missionctrl/ai-image.git
   ```

2. **Navigate to the Project Directory**

   ```
   cd ai-image
   ```

3. **Set Up the Environment**

   Ensure you have the necessary environment variables. Create a `.env` file in the project root directory with the following variables:

   ```
   HUGGINGFACE_TOKEN=<your token>
   ```

4. **Build and Run the Docker Containers**

   ```
   ./run.sh
   ```

   This script performs the following actions:
   - Activates a virtual environment.
   - Starts the Celery worker.
   - Runs the Uvicorn server with multiple workers and automatic reloading.

5. **Access the Application**

   Open your browser and navigate to `http://localhost:8888` to use the application.

## Usage

1. **Generating Images**

   - Enter a text prompt in the input field and submit the form.
   - The app will display a loading indicator while the image is being generated.
   - Once the image is ready, it will be displayed along with the prompt details.

2. **Viewing Images**

   - Click on a thumbnail to view the full-size image with details.
   - The full-size view includes options to show or hide details about the prompt, description, and aspect ratio.

3. **Managing Images**

   - Use the "Clear Images" button to delete all images from local storage and the server.
   - Click the delete icon on individual thumbnails to remove specific images.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you would like to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
