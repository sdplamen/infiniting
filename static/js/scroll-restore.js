    window.addEventListener('beforeunload', () => {
    sessionStorage.setItem('scrollpos', window.scrollY);
    sessionStorage.setItem('scrollpath', window.location.pathname);
});

document.addEventListener('DOMContentLoaded', () => {
    const scrollpos = sessionStorage.getItem('scrollpos');
    const scrollpath = sessionStorage.getItem('scrollpath');
    if (scrollpos && scrollpath === window.location.pathname) {
        window.scrollTo(0, parseInt(scrollpos, 10));
        sessionStorage.removeItem('scrollpos');
        sessionStorage.removeItem('scrollpath');
    }
});