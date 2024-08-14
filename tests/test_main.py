# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from main import app
import os
import tempfile

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

def test_static_files():
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_images():
    # Create a temporary image file
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "image.jpg")
    with open(image_path, "wb") as f:
        # Create a simple image file (e.g. a 1x1 pixel image)
        f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d \x1a\x1c $.' \x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xc0\x00\x11\x08\x01\x00\x01\x03\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x1f\x10\x00\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\xff\xc4\x00\x1f\x11\x00\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?")

    # Copy the image file to the images directory
    images_dir = os.path.join(os.getcwd(), "frontend/images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    image_file_path = os.path.join(images_dir, "image.jpg")
    os.replace(image_path, image_file_path)

    # Test that the image file is reachable from the endpoint
    response = client.get("/images/image.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")

    # Clean up the temporary image file
    os.remove(image_file_path)
    os.rmdir(temp_dir)

def test_api_routes():
    response = client.get("/api/some_route")
    assert response.status_code == 404  # assuming no routes are defined yet

def test_env_vars():
    # test that env vars are loaded correctly
    import os
    assert os.getenv("HUGGINGFACE_TOKEN") is not None  # replace with actual env var name
