document.addEventListener('DOMContentLoaded', () => {
    const promptForm = document.getElementById("promptForm");
    const baseUrl = 'http://aesync.servebeer.com:8888'; // Base URL for API endpoints

    function applyTheme(theme) {
        if (theme === 'dark') {
            $('body').removeClass('light-theme').addClass('dark-theme');
            $('.theme-selector').removeClass('light-theme').addClass('dark-theme');
        } else {
            $('body').removeClass('dark-theme').addClass('light-theme');
            $('.theme-selector').removeClass('dark-theme').addClass('light-theme');
        }
    }

    // Load theme from local storage
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
    $('#themeSelector').val(savedTheme);

    // Change theme when the dropdown value changes
    $('#themeSelector').change(function() {
        const selectedTheme = $(this).val();
        applyTheme(selectedTheme);
        localStorage.setItem('theme', selectedTheme);
    });

    // Load images from local storage on page load
    loadThumbnails();

    promptForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const prompt = document.getElementById("prompt").value;
        const aspectRatio = document.getElementById("aspectRatio").value;
        const apiKey = 'your-api-key-here'; // Replace with actual API key
        const usePromptRefiner = document.getElementById("usePromptRefiner").checked;

        try {
            const response = await fetch(`${baseUrl}/generate-image`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${apiKey}`
                },
                body: JSON.stringify({ prompt, aspectRatio, usePromptRefiner })
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
            const statusResponse = await fetch(`${baseUrl}/task-status/${taskId}`);
    
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
    
                if (statusData.status === 'SUCCESS') {
                    const { image_url: imageUrl, description, refined_prompt: refinedPrompt } = statusData.result;
                    document.querySelector('.loading-dots').style.display = 'none';
                    document.querySelector('.button-text').style.display = 'block';
                    displayImage(`${baseUrl}${imageUrl}`, description, refinedPrompt, aspectRatio, prompt);
                    saveToLocalStorage(`${baseUrl}${imageUrl}`, prompt, description, refinedPrompt, aspectRatio);
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
    
    function displayImage(imageUrl, description, refinedPrompt, aspectRatio, prompt) {
        showFullImage(imageUrl, description, refinedPrompt, aspectRatio, prompt);
    }

    function saveToLocalStorage(imageUrl, prompt, description, refinedPrompt, aspectRatio) {
        const images = JSON.parse(localStorage.getItem("images")) || [];
        images.unshift({ imageUrl, prompt, description, refinedPrompt, aspectRatio });
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
                const response = await fetch(`${baseUrl}/delete-images/`, {
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
                const response = await fetch(`${baseUrl}/delete-images/`, {
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
        // Get the images from local storage
        const images = JSON.parse(localStorage.getItem("images")) || [];
        
        // Get the thumbnails container and clear existing thumbnails
        const thumbnailsContainer = document.getElementById('thumbnails-container');
        const thumbnails = document.getElementById('thumbnails');
        thumbnails.innerHTML = '';
    
        // Show or hide the "Clear Images" button
        const clearButton = document.getElementById('clearThumbnails');
        if (images.length > 0) {
            // Show button if there are images
            if (!clearButton) {
                const newClearButton = document.createElement('button');
                newClearButton.id = 'clearThumbnails';
                newClearButton.className = 'clear-images-button';
                newClearButton.textContent = 'Clear Images';
                newClearButton.addEventListener('click', () => {
                    // Clear images from local storage and refresh thumbnails
                    localStorage.removeItem('images');
                    loadThumbnails(); // Refresh thumbnails
                });
                thumbnailsContainer.prepend(newClearButton);
            } else {
                clearButton.style.display = 'block';
            }
        } else {
            // Hide button if no images
            if (clearButton) {
                clearButton.style.display = 'none';
            }
        }
    
        // Add new thumbnails
        images.forEach((img, index) => {
            const thumbContainer = document.createElement('div');
            thumbContainer.className = 'thumbnail-container';
    
            const thumb = document.createElement('img');
            thumb.src = img.imageUrl;
            thumb.alt = "Thumbnail";
            thumb.className = 'thumbnail';
            thumb.addEventListener('click', () => showFullImage(img.imageUrl, img.description, img.refinedPrompt, img.aspectRatio, img.prompt));
    
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
    
        thumbnails.style.display = 'grid'; // Ensure thumbnails container is visible
    }

    function showFullImage(imageUrl, description, refinedPrompt, aspectRatio, prompt) {
        const fullImageContainer = document.createElement('div');
        fullImageContainer.className = 'full-image-overlay';

        const imageContainer = document.createElement('div');
        imageContainer.className = 'full-image-container theme-selector';

        const closeButton = document.createElement('div');
        closeButton.className = 'close-button';
        closeButton.textContent = '×';
        imageContainer.appendChild(closeButton);

        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button theme-selector';
        copyButton.innerHTML = '📋'; // You can use any copy icon or emoji here
        copyButton.title = 'Copy Prompt';

        copyButton.addEventListener('click', () => {
            document.getElementById('prompt').value = prompt;
            fullImageContainer.remove(); // Close the overlay
        });

        let combinedPrompt = `<br /><strong>Original Prompt</strong><hr>${prompt}`;
        if (refinedPrompt !== prompt && refinedPrompt.trim() !== '') {
            combinedPrompt += `<br /><br /><strong>Refined Prompt</strong><hr> ${refinedPrompt}`;
        }

        const promptElement = createTextElement('full-image-prompt', combinedPrompt);
        promptElement.prepend(copyButton);
        const descriptionElement = createTextElement('full-image-description', `<strong>Description</strong><hr>${description}`);
        const aspectRatioElement = createTextElement('full-image-aspect-ratio', `<strong>Aspect Ratio</strong><hr>${aspectRatio}`);

        const textInfoContainer = document.createElement('div');
        textInfoContainer.className = 'text-info-container';
        textInfoContainer.append(promptElement, descriptionElement, aspectRatioElement);

        const promptButton = document.createElement('button');
        promptButton.className = 'toggle-button theme-selector';
        promptButton.textContent = 'Show Prompt';
        promptButton.addEventListener('click', () => {
            const isHidden = promptElement.classList.toggle('hidden');
            promptButton.textContent = isHidden ? 'Show Prompt' : 'Hide Prompt Details';
        });

        const downloadButton = document.createElement('button');
        downloadButton.className = 'download-button theme-selector';
        downloadButton.textContent = 'Download Image';
        downloadButton.addEventListener('click', () => {
            const link = document.createElement('a');
            link.href = imageUrl.replace(/original_/i, '');
            link.download = `image_${Date.now()}.png`;
            link.click();
        });

        const descriptionButton = createToggleButton(descriptionElement, 'Show Description');
        const aspectRatioButton = createToggleButton(aspectRatioElement, 'Show Aspect Ratio');

        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'toggle-container';
        toggleContainer.append(promptButton, descriptionButton, aspectRatioButton, downloadButton);

        const textContainer = document.createElement('div');
        textContainer.className = 'text-container';
        textContainer.append(toggleContainer, textInfoContainer);

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
        let savedTheme = localStorage.getItem('theme') || 'light';
        applyTheme(savedTheme);
    }

    function createTextElement(className, textContent) {
        const element = document.createElement('p');
        element.className = `${className} theme-selector hidden`;
        element.innerHTML = textContent;
        return element;
    }

    function createToggleButton(targetElement, initialText) {
        const button = document.createElement('button');
        button.className = 'toggle-button theme-selector';
        button.textContent = initialText;
        button.addEventListener('click', () => {
            const isHidden = targetElement.classList.toggle('hidden');
            button.textContent = isHidden ? `Show ${initialText.split(' ')[1]}` : `Hide ${initialText.split(' ')[1]}`;
        });
        return button;
    }
});
