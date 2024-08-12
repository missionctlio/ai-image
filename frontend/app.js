document.addEventListener('DOMContentLoaded', () => {
    const promptForm = document.getElementById("promptForm");
    const thumbnails = document.getElementById("thumbnails");

    // Load images from local storage on page load
    loadThumbnails();

    promptForm.addEventListener("submit", async function(event) {
        event.preventDefault();
        const prompt = document.getElementById("prompt").value;
        const apiKey = 'your-api-key-here'; // Replace with actual API key

        // Show loading icon
        document.querySelector('.loading-dots').style.display = 'flex';
        document.querySelector('.button-text').style.display = 'none';

        try {
            const response = await fetch("/generate-image", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${apiKey}`
                },
                body: JSON.stringify({ prompt })
            });

            if (response.ok) {
                const data = await response.json();
                const imageUrl = data.image_url;
                const description = data.description;
                displayImage(imageUrl, description);
                saveToLocalStorage(imageUrl, prompt, description);
            } else {
                alert("Error generating image. Please try again.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred. Please try again.");
        } finally {
            document.querySelector('.loading-dots').style.display = 'none';
            document.querySelector('.button-text').style.display = 'block';
        }
    });

    function displayImage(imageUrl, description, prompt) {
        showFullImage(imageUrl, description, prompt);
    }

    function saveToLocalStorage(imageUrl, prompt, description) {
        let images = JSON.parse(localStorage.getItem("images")) || [];
        images.unshift({ imageUrl, prompt, description });
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
            descriptionContainer.textContent = img.description;

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

            thumb.addEventListener('click', () => showFullImage(img.imageUrl, img.description, img.prompt));
            thumbnails.appendChild(thumbContainer);
        });
    }

    function deleteImage(index) {
        let images = JSON.parse(localStorage.getItem("images")) || [];
        images.splice(index, 1);
        localStorage.setItem("images", JSON.stringify(images));
        loadThumbnails();
    }

    function showFullImage(imageUrl, description, prompt) {
        // Create the full image overlay
        const fullImageContainer = document.createElement('div');
        fullImageContainer.className = 'full-image-overlay';
    
        // Create the image container with the gradient background
        const imageContainer = document.createElement('div');
        imageContainer.className = 'full-image-container';
    
        // Create the prompt and description elements
        const promptElement = document.createElement('p');
        promptElement.className = 'full-image-prompt';
        promptElement.textContent = `User Prompt: ${prompt}`;
    
        const descriptionElement = document.createElement('p');
        descriptionElement.className = 'full-image-description';
        descriptionElement.textContent = `Generated Description: ${description}`;
    
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
        textContainer.appendChild(promptElement);
        textContainer.appendChild(descriptionElement);
    
        // Append elements to the image container
        imageContainer.appendChild(textContainer);
        imageContainer.appendChild(fullImage);
    
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
