# Image Generation App

## Overview

This application allows users to generate images based on text prompts. It integrates with an image generation API, displays results with detailed descriptions, and provides functionality for managing generated images.

### Screenshots
<p align="left">
<a href="https://github.com/user-attachments/assets/78c202c2-7baf-48a3-895c-364629d6d642">
  <img src="https://github.com/user-attachments/assets/78c202c2-7baf-48a3-895c-364629d6d642" alt="C8n7eb5Lgy" style="display: inline-block; width: 45%;">
</a>
<a href="https://github.com/user-attachments/assets/5475051c-e168-4d7a-aff9-bbbf77ce0c85">
  <img src="https://github.com/user-attachments/assets/5475051c-e168-4d7a-aff9-bbbf77ce0c85" alt="chrome_hGvBBSAYnw" style="display: inline-block; width: 45%;">
</a>
</p>




## Features

- **Image Generation**: Submit prompts to generate images via the `/generate-image` API endpoint.
- **Prompt Handling**: Displays both the original and refined prompts combined with a line break.
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


- **Database**:
  - Local Storage (for saving images and metadata)

## API Endpoints

### POST /generate-image

Generates an image based on the provided prompt and aspect ratio.

**Request Body:**

```
{
    "prompt": "string",
    "aspectRatio": "string"
}
```

**Response:**

```
{
    "task_id": "string"
}
```

### GET /task-status/{taskId}

Checks the status of the image generation task.

**URL Parameters:**
- `taskId`: The ID of the task to check.

**Response:**

```
{
    "status": "string",
    "result": {
        "image_url": "string",
        "description": "string",
        "refined_prompt": "string"
    }
}
```

### DELETE /delete-images/

Deletes images from the server.

**Request Body:**

```
{
    "image_ids": ["string"]
}
```

**Response:**

```
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

- **Backend**:
  - `app/api.py`: FastAPI application entry point.

- **Inference**:
  - **Image**:
    - `app/inference/image/diffuser.py`: Image diffusion logic using the Black-Forest-Labs Flux Diffuser.
    - `app/inference/image/model.py`: Model-related logic.
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
  
- **Startup** 
  - `run.sh`: Script to build and run Docker containers.

## Setup and Installation

### Prerequisites

- Docker
- Docker Compose
- Python 3.x

### Running the Application

1. **Clone the Repository**

   ```
   git clone https://github.com/your-username/image-generation-app.git
   ```

2. **Navigate to the Project Directory**

   ```
   cd image-generation-app
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
