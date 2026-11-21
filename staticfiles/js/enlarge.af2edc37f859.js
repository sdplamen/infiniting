document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.photo-display-large');

    images.forEach(image => {
        image.addEventListener('click', function() {
            this.classList.toggle('enlarged');
        });
    });
});