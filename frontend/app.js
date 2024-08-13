document.addEventListener('DOMContentLoaded', () => {
    const promptForm = document.getElementById("promptForm");
    const thumbnails = document.getElementById("thumbnails");

    // Load images from local storage on page load
    loadThumbnails();

    promptForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const prompt = document.getElementById("prompt").value;
        const aspectRatio = document.getElementById("aspectRatio").value;
        const apiKey = 'your-api-key-here'; // Replace with actual API key

        try {
            const response = await fetch("/generate-image", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${apiKey}`
                },
                body: JSON.stringify({ prompt, aspectRatio })
            });

            if (response.ok) {
                const data = await response.json();
                const taskId = data.task_id;

                // Show loading indicator
                document.querySelector('.loading-dots').style.display = 'flex';
                document.querySelector('.button-text').style.display = 'none';
                pollTaskStatus(taskId, prompt, aspectRatio);
            } else {
                alert("Error generating image. Please try again.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred. Please try again.");
        }
    });

    async function pollTaskStatus(taskId, prompt, aspectRatio, retryCount = 0) {
        const maxRetries = 3;
        const maxPollDuration = 4 * 60 * 1000; // 4 minutes
        const retryDelay = 5000; // 5 seconds
    
        try {
            const statusResponse = await fetch(`/task-status/${taskId}`);
    
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
    
                if (statusData.status === 'SUCCESS') {
                    const { image_url: imageUrl, description } = statusData.result;
                    document.querySelector('.loading-dots').style.display = 'none';
                    document.querySelector('.button-text').style.display = 'block';
                    displayImage(imageUrl, description, aspectRatio, prompt);
                    saveToLocalStorage(imageUrl, prompt, description, aspectRatio);
                } else if (statusData.status === 'PENDING') {
                    const nextRetryTime = Date.now() + retryDelay;
                    if (nextRetryTime - Date.now() <= maxPollDuration) {
                        setTimeout(() => pollTaskStatus(taskId, prompt, aspectRatio, retryCount), retryDelay);
                    } else {
                        alert('Polling timed out. Please try again later.');
                    }
                } else if (retryCount < maxRetries) {
                    console.warn(`Attempt ${retryCount + 1} failed. Retrying...`);
                    setTimeout(() => pollTaskStatus(taskId, prompt, aspectRatio, retryCount + 1), retryDelay);
                } else {
                    alert(`Error: ${statusData.result}. Max retries reached.`);
                }
            } else if (statusResponse.status === 500) {
                // Handle 500 Internal Server Error with retry
                const nextRetryTime = Date.now() + retryDelay;
                if (nextRetryTime - Date.now() <= maxPollDuration) {
                    setTimeout(() => pollTaskStatus(taskId, prompt, aspectRatio, retryCount), retryDelay);
                } else {
                    alert('Server error. Max retries reached.');
                }
            } else {
                alert("Error retrieving task status. Please try again.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while checking task status.");
        }
    }
    
    function displayImage(imageUrl, description, aspectRatio, prompt) {
        showFullImage(imageUrl, description, aspectRatio, prompt);
    }

    function saveToLocalStorage(imageUrl, prompt, description, aspectRatio) {
        const images = JSON.parse(localStorage.getItem("images")) || [];
        images.unshift({ imageUrl, prompt, description, aspectRatio });
        localStorage.setItem("images", JSON.stringify(images));
        loadThumbnails(); // Only load thumbnails after saving an image
    }

    async function deleteImage(index) {
        const images = JSON.parse(localStorage.getItem("images")) || [];
        if (index >= 0 && index < images.length) {
            const imageUrl = images[index].imageUrl;
            const imageId = imageUrl.split('/').pop();
            const originalImageId = imageId.replace('original_', '');

            try {
                const response = await fetch('/delete-images/', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ image_ids: [imageId, originalImageId] })
                });

                if (response.ok) {
                    images.splice(index, 1);
                    localStorage.setItem("images", JSON.stringify(images));
                    loadThumbnails(); // Only load thumbnails after deleting an image
                } else {
                    alert("Error deleting image. Please try again.");
                }
            } catch (error) {
                console.error("Error:", error);
                alert("An error occurred while deleting the image.");
            }
        }
    }
    
    const clearThumbnailsButton = document.getElementById("clearThumbnails");
    clearThumbnailsButton.addEventListener('click', async () => {
        const images = JSON.parse(localStorage.getItem("images")) || [];
        if (images.length > 0) {
            const imageIds = images.flatMap(img => {
                const imageId = img.imageUrl.split('/').pop();
                const originalImageId = imageId.replace('original_', '');
                return [imageId, originalImageId];
            });

            try {
                const response = await fetch('/delete-images/', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ image_ids: imageIds })
                });

                if (response.ok) {
                    localStorage.removeItem("images");
                    loadThumbnails(); // Only load thumbnails after clearing all images
                } else {
                    alert("Error clearing images. Please try again.");
                }
            } catch (error) {
                console.error("Error:", error);
                alert("An error occurred while clearing the images.");
            }
        }
    });

    function loadThumbnails() {
        const images = JSON.parse(localStorage.getItem("images")) || [];
        thumbnails.innerHTML = '<button id="clearThumbnails" class="clear-images-button">Clear Images</button>';

        if (images.length > 0) {
            images.forEach((img, index) => {
                const thumbContainer = document.createElement('div');
                thumbContainer.className = 'thumbnail-container';

                const thumb = document.createElement('img');
                thumb.src = img.imageUrl;
                thumb.alt = "Thumbnail";
                thumb.className = 'thumbnail';
                thumb.addEventListener('click', () => showFullImage(img.imageUrl, img.description, img.aspectRatio, img.prompt));

                const descriptionContainer = document.createElement('div');
                descriptionContainer.className = 'description-container';
                descriptionContainer.textContent = `Aspect Ratio: ${img.aspectRatio}`;

                const deleteIcon = document.createElement('div');
                deleteIcon.className = 'delete-icon';
                deleteIcon.textContent = '×';
                deleteIcon.dataset.index = index;
                deleteIcon.addEventListener('click', () => deleteImage(index));

                thumbContainer.append(thumb, descriptionContainer, deleteIcon);
                thumbnails.appendChild(thumbContainer);
            });
            thumbnails.style.display = 'block'; // Ensure thumbnails container is visible
        } else {
            thumbnails.style.display = 'none';
        }
    }

    function showFullImage(imageUrl, description, aspectRatio, prompt) {
        const fullImageContainer = document.createElement('div');
        fullImageContainer.className = 'full-image-overlay';

        const imageContainer = document.createElement('div');
        imageContainer.className = 'full-image-container';

        const closeButton = document.createElement('div');
        closeButton.className = 'close-button';
        closeButton.textContent = '×';
        imageContainer.appendChild(closeButton);

        const promptElement = createTextElement('full-image-prompt', `Prompt: ${prompt}`);
        const descriptionElement = createTextElement('full-image-description', `Description: ${description}`);
        const aspectRatioElement = createTextElement('full-image-aspect-ratio', `Aspect Ratio: ${aspectRatio}`);

        const textInfoContainer = document.createElement('div');
        textInfoContainer.className = 'text-info-container';
        textInfoContainer.append(promptElement, descriptionElement, aspectRatioElement);

        const buttons = [
            createToggleButton(promptElement, 'Show Prompt'),
            createToggleButton(descriptionElement, 'Show Description'),
            createToggleButton(aspectRatioElement, 'Show Aspect Ratio')
        ];

        const downloadButton = document.createElement('button');
        downloadButton.className = 'download-button';
        downloadButton.textContent = 'Download Image';
        downloadButton.addEventListener('click', () => {
            const link = document.createElement('a');
            link.href = imageUrl.replace(/original_/i, '');
            link.download = `image_${Date.now()}.png`;
            link.click();
        });

        const textContainer = document.createElement('div');
        textContainer.className = 'text-container';
        textContainer.append(...buttons, downloadButton, textInfoContainer);

        const fullImage = document.createElement('img');
        fullImage.src = imageUrl;
        fullImage.alt = 'Full Image';
        fullImage.className = 'full-image-img';

        imageContainer.append(fullImage, textContainer);
        fullImageContainer.appendChild(imageContainer);
        document.body.appendChild(fullImageContainer);

        fullImageContainer.addEventListener('click', (e) => {
            if (e.target === fullImageContainer || e.target === closeButton) {
                fullImageContainer.remove();
            }
        });
    }

    function createTextElement(className, textContent) {
        const element = document.createElement('p');
        element.className = `${className} hidden`;
        element.textContent = textContent;
        return element;
    }

    function createToggleButton(targetElement, initialText) {
        const button = document.createElement('button');
        button.className = 'toggle-button';
        button.textContent = initialText;
        button.addEventListener('click', () => {
            const isHidden = targetElement.classList.toggle('hidden');
            button.textContent = isHidden ? `Show ${initialText.split(' ')[1]}` : `Hide ${initialText.split(' ')[1]}`;
        });
        return button;
    }
});
