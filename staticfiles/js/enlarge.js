document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.photo-display-large');
    const body = document.body; // Get the body element

    images.forEach(image => {
        image.addEventListener('click', function() {
            this.classList.toggle('enlarged');

            if (this.classList.contains('enlarged')) {
                // Create and append overlay when image is enlarged
                const overlay = document.createElement('div');
                overlay.classList.add('enlarged-overlay');
                overlay.addEventListener('click', function() {
                    // Remove enlarged class from image and remove overlay when overlay is clicked
                    image.classList.remove('enlarged');
                    body.removeChild(overlay);
                });
                body.appendChild(overlay);
            } else {
                // Remove overlay when image is shrunk
                const existingOverlay = document.querySelector('.enlarged-overlay');
                if (existingOverlay) {
                    body.removeChild(existingOverlay);
                }
            }
        });
    });
});