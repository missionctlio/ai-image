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
                displayImage(imageUrl, prompt);
                saveToLocalStorage(imageUrl, prompt);
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

    function displayImage(imageUrl, prompt) {
        showFullImage(imageUrl, prompt); // Display the image in a lightbox
    }

    function saveToLocalStorage(imageUrl, prompt) {
        let images = JSON.parse(localStorage.getItem("images")) || [];
        images.unshift({ imageUrl, prompt });
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
            const deleteIcon = document.createElement('div');
            deleteIcon.className = 'delete-icon';
            deleteIcon.textContent = '✖';
            deleteIcon.dataset.index = index;
            deleteIcon.addEventListener('click', () => deleteImage(index));

            // Create thumbnail container
            const thumbContainer = document.createElement('div');
            thumbContainer.className = 'thumbnail-container';
            thumbContainer.appendChild(thumb);
            thumbContainer.appendChild(deleteIcon);
            
            thumb.addEventListener('click', () => showFullImage(img.imageUrl, img.prompt));
            thumbnails.appendChild(thumbContainer);
        });
    }

    function deleteImage(index) {
        let images = JSON.parse(localStorage.getItem("images")) || [];
        images.splice(index, 1);
        localStorage.setItem("images", JSON.stringify(images));
        loadThumbnails();
    }

    function showFullImage(imageUrl, prompt) {
        const fullImageContainer = document.createElement('div');
        fullImageContainer.className = 'full-image-overlay';
        fullImageContainer.innerHTML = `
            <div class="full-image-container">
                <p class="full-image-prompt">${prompt}</p>
                <img src="${imageUrl}" alt="Full Image" class="full-image-img" />
            </div>
        `;
        fullImageContainer.addEventListener('click', () => {
            document.body.removeChild(fullImageContainer);
        });
        document.body.appendChild(fullImageContainer);
    }
    
    
});
