# Image Generation and Management Web Application

## Overview

This project is a web application that generates and manages images based on user prompts. It allows users to submit prompts, view generated images, and manage their image collection. The application includes features for displaying image details, deleting individual images, and clearing all images.

## Features

- **Image Generation**: Submit prompts and generate images with various aspect ratios.
- **Image Display**: View full-sized images with associated prompts, descriptions, and aspect ratios.
- **Image Management**: Delete individual images or clear all images from the collection.
- **Responsive Design**: Optimized for both desktop and mobile views.

## Technologies Used

- **Frontend**:
  - HTML
  - CSS
  - JavaScript

- **Backend**:
  - Python
  - FastAPI
  - Celery
  - Redis

- **Database**: 
  - Local Storage (for storing images and metadata temporarily)

- **Containerization**:
  - Docker
  - Docker Compose

## Setup and Running

### Prerequisites

Ensure you have the following installed:
- Docker
- Docker Compose
- Python 3.8 or higher

### Running the Application

1. **Clone the Repository**

   ```
   git clone https://github.com/your-repo/image-management-app.git
   cd image-management-app
   ```

2. **Set Up the Environment**

   Create a virtual environment and install dependencies:

   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create Docker Containers**

   Start the Docker containers in detached mode:

   ```
   docker-compose up -d
   ```

4. **Start Celery Worker and Uvicorn Server**

   Use the `run.sh` script to start the Celery worker and Uvicorn server:

   ```
   ./run.sh
   ```

   Alternatively, you can run the commands manually:

   ```
   source .venv/bin/activate
   celery -A backend.celery_config.celery worker --pool=solo --loglevel=INFO &
   uvicorn backend.main:app --workers 4 --host 0.0.0.0 --port 8888 --reload-dir backend
   ```

## Endpoints

### POST `/generate-image`

**Description**: Submits a prompt and aspect ratio to generate an image.

**Request Body**:

  ```
  {
    "prompt": "string",
    "aspectRatio": "string"
  }
  ```

  - **prompt**: The text prompt to generate the image from.
  - **aspectRatio**: The desired aspect ratio of the generated image (e.g., "16:9", "4:3").

**Response**:

  ```
  {
    "task_id": "string"
  }
  ```

  - **task_id**: A unique identifier for the image generation task. Use this ID to check the status of the task.

**Errors**:
- `400 Bad Request`: Invalid request parameters.
- `500 Internal Server Error`: Server encountered an error.

### DELETE `/delete-images/`

**Description**: Deletes specified images.

**Request Body**:

  ```
  {
    "image_ids": [
      "string",
      "string"
    ]
  }
  ```

  - **image_ids**: An array of image IDs to delete. This array should include both the original image ID and any variations (e.g., with or without "original_").

**Response**:

  ```
  {
    "success": true
  }
  ```

  - **success**: Indicates whether the deletion operation was successful.

**Errors**:
- `400 Bad Request`: Invalid request parameters.
- `404 Not Found`: One or more specified images were not found.
- `500 Internal Server Error`: Server encountered an error.

### GET `/task-status/{taskId}`

**Description**: Retrieves the status of a specific image generation task.

**Response**:

  ```
  {
    "status": "SUCCESS" | "PENDING" | "FAILED",
    "result": {
      "image_url": "string",
      "description": "string"
    }
  }
  ```

  - **status**: The current status of the task.
  - **result**: Contains `image_url` and `description` if the task is successful.

## Notes

- Replace `https://github.com/your-repo/image-management-app.git` with the actual URL of your repository.
- Ensure that environment variables and API keys are properly configured.
- For any issues or feature requests, please open an issue on the project's GitHub page.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

