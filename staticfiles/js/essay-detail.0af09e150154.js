/*
 * Essay page: returning from the lightbox lands on /essays/<id>/#frame-N.
 * The frames are lazy-loaded and have no fixed height, so the browser's own
 * jump to #frame-N happens before the photos above it have their size, and
 * ends up a frame or two early. Load those photos first, then scroll.
 */
(function () {
    'use strict';

    function settle(img) {
        if (img.complete) return Promise.resolve();
        return new Promise(function (resolve) {
            img.addEventListener('load', resolve, { once: true });
            img.addEventListener('error', resolve, { once: true });
        });
    }

    function goToFrame() {
        var match = /^#frame-(\d+)$/.exec(window.location.hash);
        var target = match && document.getElementById('frame-' + match[1]);
        if (!target) return;

        var frames = Array.prototype.slice.call(document.querySelectorAll('[id^="frame-"]'));
        var upTo = frames.indexOf(target);
        var images = frames.slice(0, upTo + 1).map(function (frame) {
            var img = frame.querySelector('img');
            if (img) img.loading = 'eager';
            return img;
        }).filter(Boolean);

        Promise.all(images.map(settle)).then(function () {
            target.scrollIntoView({ block: 'start' });
        });
    }

    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    goToFrame();
    window.addEventListener('hashchange', goToFrame);
})();
