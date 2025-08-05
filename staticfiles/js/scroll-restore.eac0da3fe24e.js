    document.addEventListener("DOMContentLoaded", () => {
        const scrollpos = sessionStorage.getItem('scrollpos');
        if (scrollpos !== null) {
            const restoreScroll = () => {
                window.scrollTo({ top: parseInt(scrollpos, 10), behavior: 'auto' });
                sessionStorage.removeItem('scrollpos');
            };
            // Wait for images or other resources to load
            window.addEventListener('load', restoreScroll, { once: true });
        }
    });