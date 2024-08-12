document.addEventListener('DOMContentLoaded', () => {
    const promptForm = document.getElementById("promptForm");
    const thumbnails = document.getElementById("thumbnails");

    // Load images from local storage on page load
    loadThumbnails();

    promptForm.addEventListener("submit", async function(event) {
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

                // Poll for task status
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

    async function pollTaskStatus(taskId, prompt, aspectRatio) {
        try {
            const statusResponse = await fetch(`/task-status/${taskId}`);
            
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                // Show loading icon
                if (statusData.status === 'SUCCESS') {
                    const imageUrl = statusData.result.image_url;
                    console.log(statusData.result.imageUrl)
                    const description = statusData.result.description;
                    document.querySelector('.loading-dots').style.display = 'none';
                    document.querySelector('.button-text').style.display = 'block';
                    displayImage(imageUrl, description, aspectRatio, prompt);
                    saveToLocalStorage(imageUrl, prompt, description, aspectRatio);
                } else if (statusData.status === 'FAILURE') {
                    alert(`Error: ${statusData.result}`);
                } else {
                    // Poll again if status is still processing
                    setTimeout(() => pollTaskStatus(taskId, prompt, aspectRatio), 2000); // Poll every 2 seconds
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
        let images = JSON.parse(localStorage.getItem("images")) || [];
        images.unshift({ imageUrl, prompt, description, aspectRatio });
        localStorage.setItem("images", JSON.stringify(images));
        loadThumbnails();
    }

    function loadThumbnails() {
        const images = JSON.parse(localStorage.getItem("images")) || [];
        thumbnails.innerHTML = '';
        images.forEach((img, index) => {
            const thumb = document.createElement('img');
            thumb.src = img.imageUrl;
            thumb.alt = "Thumbnail";
            thumb.className = 'thumbnail';

            const descriptionContainer = document.createElement('div');
            descriptionContainer.className = 'description-container';
            descriptionContainer.textContent = `Aspect Ratio: ${img.aspectRatio}`;

            const deleteIcon = document.createElement('div');
            deleteIcon.className = 'delete-icon';
            deleteIcon.textContent = '✖';
            deleteIcon.dataset.index = index;
            deleteIcon.addEventListener('click', () => deleteImage(index));

            // Create thumbnail container
            const thumbContainer = document.createElement('div');
            thumbContainer.className = 'thumbnail-container';
            thumbContainer.appendChild(thumb);
            thumbContainer.appendChild(descriptionContainer);
            thumbContainer.appendChild(deleteIcon);

            thumb.addEventListener('click', () => showFullImage(img.imageUrl, img.description, img.aspectRatio, img.prompt));
            thumbnails.appendChild(thumbContainer);
        });
    }

    function deleteImage(index) {
        let images = JSON.parse(localStorage.getItem("images")) || [];
        images.splice(index, 1);
        localStorage.setItem("images", JSON.stringify(images));
        loadThumbnails();
    }

    function showFullImage(imageUrl, description, aspectRatio, prompt) {
        // Create the full image overlay
        const fullImageContainer = document.createElement('div');
        fullImageContainer.className = 'full-image-overlay';
        
        // Create the image container with the gradient background
        const imageContainer = document.createElement('div');
        imageContainer.className = 'full-image-container';
        
        // Create the prompt and description elements
        const promptElement = document.createElement('p');
        promptElement.className = 'full-image-prompt';
        promptElement.textContent = `Prompt: ${prompt}`;
        
        const descriptionElement = document.createElement('p');
        descriptionElement.className = 'full-image-description';
        descriptionElement.textContent = `Description: ${description}`;
        
        const aspectRatioElement = document.createElement('p');
        aspectRatioElement.className = 'full-image-aspect-ratio';
        aspectRatioElement.textContent = `Aspect Ratio: ${aspectRatio}`;
        
        // Create the buttons for toggling visibility
        const promptButton = document.createElement('button');
        promptButton.className = 'toggle-button';
        promptButton.textContent = 'Show Prompt';
        promptButton.addEventListener('click', () => {
            promptElement.classList.toggle('visible');
            promptButton.textContent = promptElement.classList.contains('visible') ? 'Hide Prompt' : 'Show Prompt';
        });
        
        const descriptionButton = document.createElement('button');
        descriptionButton.className = 'toggle-button';
        descriptionButton.textContent = 'Show Description';
        descriptionButton.addEventListener('click', () => {
            descriptionElement.classList.toggle('visible');
            descriptionButton.textContent = descriptionElement.classList.contains('visible') ? 'Hide Description' : 'Show Description';
        });
    
        const aspectRatioButton = document.createElement('button');
        aspectRatioButton.className = 'toggle-button';
        aspectRatioButton.textContent = 'Show Aspect Ratio';
        aspectRatioButton.addEventListener('click', () => {
            aspectRatioElement.classList.toggle('visible');
            aspectRatioButton.textContent = aspectRatioElement.classList.contains('visible') ? 'Hide Aspect Ratio' : 'Show Aspect Ratio';
        });
        
        // Create the download button
        const downloadButton = document.createElement('button');
        downloadButton.className = 'download-button';
        downloadButton.textContent = 'Download Image';
        downloadButton.addEventListener('click', () => {
            const link = document.createElement('a');
            link.href = imageUrl.replace(/original_/i, '');;
            link.download = `image_${Date.now()}.png`; // Optionally, you can format the filename
            link.click();
        });
        
        // Create the full image element
        const fullImage = document.createElement('img');
        fullImage.src = imageUrl;
        fullImage.alt = 'Full Image';
        fullImage.className = 'full-image-img';
        
        // Create a container for the text and buttons
        const textContainer = document.createElement('div');
        textContainer.className = 'text-container';
        
        // Append buttons and text to the text container
        textContainer.appendChild(promptButton);
        textContainer.appendChild(descriptionButton);
        textContainer.appendChild(aspectRatioButton);
        textContainer.appendChild(downloadButton); // Add download button here
        textContainer.appendChild(promptElement);
        textContainer.appendChild(descriptionElement);
        textContainer.appendChild(aspectRatioElement);
        
        // Append elements to the image container
        imageContainer.appendChild(fullImage);
        imageContainer.appendChild(textContainer);
        
        // Append the image container to the overlay
        fullImageContainer.appendChild(imageContainer);
        
        // Add an event listener to remove the overlay on click
        fullImageContainer.addEventListener('click', (event) => {
            if (event.target === fullImageContainer) {
                document.body.removeChild(fullImageContainer);
            }
        });
        
        // Append the overlay to the body
        document.body.appendChild(fullImageContainer);
    }
});
