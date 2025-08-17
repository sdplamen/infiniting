window.addEventListener('beforeunload', () => {
    sessionStorage.setItem('scrollpos', window.scrollY);
    sessionStorage.setItem('scrollpath', window.location.pathname);
});

document.addEventListener('DOMContentLoaded', () => {
    // The following code is commented out to prevent the page from restoring the scroll position on refresh.
    // The page will now scroll to the top on every refresh.
    /*
    const scrollpos = sessionStorage.getItem('scrollpos');
    const scrollpath = sessionStorage.getItem('scrollpath');
    if (scrollpos && scrollpath === window.location.pathname) {
        window.scrollTo(0, parseInt(scrollpos, 10));
        sessionStorage.removeItem('scrollpos');
        sessionStorage.removeItem('scrollpath');
    }
    */
});