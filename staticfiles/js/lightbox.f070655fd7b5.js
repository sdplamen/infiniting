/*
 * Dark-room lightbox (templates/photos/photo-full-photo.html).
 *
 *   ← / →         previous / next photo (feed order); swipe on touch screens
 *   Esc           leave the loupe, or close the lightbox
 *   click, Z      toggle the loupe at that point (Z / Enter / Space: centre)
 *   in the loupe  the image follows the mouse, drag on touch, arrows pan
 *
 * The prev/next/close links work without this script; it only adds keys,
 * the loupe and swipes. Navigation replaces the history entry, so the
 * browser's Back button returns to the page the lightbox was opened from.
 */
(function () {
    'use strict';

    var body = document.body;
    var stage = document.getElementById('lb-stage');
    var img = document.getElementById('lb-image');
    var urls = {
        prev: body.dataset.prevUrl,
        next: body.dataset.nextUrl,
        close: body.dataset.closeUrl,
    };

    var LOUPE_FACTOR = 2.5;   // at least this much bigger than the fitted view…
    var PAN_STEP = 0.12;      // …and arrow keys pan by this share of the screen
    var IDLE_MS = 2500;       // controls fade after this long without input
    var TAP_SLOP = 8;         // px a pointer may move and still count as a click

    function go(url) {
        if (url) window.location.replace(url);
    }

    // --- controls fade out while the photo is being looked at -----------------
    var idleTimer;
    function wake() {
        body.classList.remove('is-idle');
        clearTimeout(idleTimer);
        idleTimer = setTimeout(function () { body.classList.add('is-idle'); }, IDLE_MS);
    }
    ['mousemove', 'keydown', 'pointerdown'].forEach(function (type) {
        document.addEventListener(type, wake, { passive: true });
    });
    wake();

    if (!stage || !img) {
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') go(urls.close); });
        return;
    }

    // --- loupe geometry --------------------------------------------------------
    var zoomed = false;
    var scale = 1;            // CSS px per image pixel while zoomed
    var tx = 0, ty = 0;       // top-left of the zoomed image in the viewport
    var focus = { fx: 0.5, fy: 0.5 };  // image point (0..1) kept under the pointer

    function viewport() {
        return { w: stage.clientWidth, h: stage.clientHeight };
    }

    // where the fitted (object-fit: contain) image sits on screen
    function fittedBox() {
        var v = viewport();
        var fit = Math.min(v.w / img.naturalWidth, v.h / img.naturalHeight);
        var w = img.naturalWidth * fit, h = img.naturalHeight * fit;
        return { left: (v.w - w) / 2, top: (v.h - h) / 2, w: w, h: h, fit: fit };
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    // keep the image covering the screen along an axis, or centred if it's smaller
    function clampAxis(offset, size, view) {
        return size <= view ? (view - size) / 2 : clamp(offset, view - size, 0);
    }

    function render() {
        var v = viewport();
        var w = img.naturalWidth * scale, h = img.naturalHeight * scale;
        tx = clampAxis(tx, w, v.w);
        ty = clampAxis(ty, h, v.h);
        img.style.width = w + 'px';
        img.style.height = h + 'px';
        img.style.transform = 'translate3d(' + tx + 'px,' + ty + 'px,0)';
    }

    // put image point (fx, fy) under screen point (x, y)
    function pinTo(x, y) {
        tx = x - focus.fx * img.naturalWidth * scale;
        ty = y - focus.fy * img.naturalHeight * scale;
        render();
    }

    // follow the mouse: moving across the fitted photo sweeps the whole image
    function followPointer(x, y) {
        var box = fittedBox();
        focus.fx = clamp((x - box.left) / box.w, 0, 1);
        focus.fy = clamp((y - box.top) / box.h, 0, 1);
        pinTo(x, y);
    }

    function zoomIn(x, y) {
        if (!img.naturalWidth) return;          // not loaded yet
        var box = fittedBox();
        // 1:1 image pixels for grain and focus, but never less than LOUPE_FACTOR × fitted
        scale = Math.max(1, box.fit * LOUPE_FACTOR);
        zoomed = true;
        body.classList.add('is-zoomed');
        followPointer(x, y);
    }

    function zoomOut() {
        zoomed = false;
        body.classList.remove('is-zoomed');
        img.style.width = img.style.height = img.style.transform = '';
    }

    function toggleAt(x, y) {
        if (zoomed) zoomOut(); else zoomIn(x, y);
    }

    function stageCentre() {
        var v = viewport();
        return { x: v.w / 2, y: v.h / 2 };
    }

    // --- pointer: click/tap toggles, mouse follows, touch drags or swipes --------
    var down = null;   // {x, y, startTx, startTy, moved, type}

    stage.addEventListener('pointerdown', function (e) {
        if (e.button !== 0) return;
        down = { x: e.clientX, y: e.clientY, startTx: tx, startTy: ty, moved: false, type: e.pointerType };
        stage.setPointerCapture(e.pointerId);
    });

    stage.addEventListener('pointermove', function (e) {
        if (down && Math.hypot(e.clientX - down.x, e.clientY - down.y) > TAP_SLOP) down.moved = true;
        if (!zoomed) return;
        if (e.pointerType === 'mouse') {
            followPointer(e.clientX, e.clientY);
        } else if (down) {
            tx = down.startTx + (e.clientX - down.x);
            ty = down.startTy + (e.clientY - down.y);
            render();
        }
    });

    stage.addEventListener('pointerup', function (e) {
        if (!down) return;
        var dx = e.clientX - down.x, dy = e.clientY - down.y, start = down;
        down = null;
        if (!start.moved) {
            toggleAt(e.clientX, e.clientY);
        } else if (!zoomed && start.type !== 'mouse' && Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) {
            go(dx < 0 ? urls.next : urls.prev);   // swipe left = next, as in the feed
        } else if (zoomed && start.type !== 'mouse') {
            // remember which image point is now centred, for resizes and key panning
            var c = stageCentre();
            focus.fx = (c.x - tx) / (img.naturalWidth * scale);
            focus.fy = (c.y - ty) / (img.naturalHeight * scale);
        }
    });

    stage.addEventListener('pointercancel', function () { down = null; });

    // --- keyboard ----------------------------------------------------------------
    function panBy(dx, dy) {
        var v = viewport();
        tx -= dx * v.w * PAN_STEP;
        ty -= dy * v.h * PAN_STEP;
        render();
    }

    document.addEventListener('keydown', function (e) {
        if (e.altKey || e.ctrlKey || e.metaKey) return;  // leave browser shortcuts alone
        var c;
        switch (e.key) {
            case 'ArrowLeft':  zoomed ? panBy(-1, 0) : go(urls.prev); break;
            case 'ArrowRight': zoomed ? panBy(1, 0) : go(urls.next); break;
            case 'ArrowUp':    if (!zoomed) return; panBy(0, -1); break;
            case 'ArrowDown':  if (!zoomed) return; panBy(0, 1); break;
            case 'Escape':     zoomed ? zoomOut() : go(urls.close); break;
            case 'z': case 'Z': case 'Enter': case ' ':
                // Enter/Space on a focused link should still follow that link
                if ((e.key === 'Enter' || e.key === ' ') && document.activeElement && document.activeElement.tagName === 'A') return;
                c = stageCentre();
                toggleAt(c.x, c.y);
                break;
            default: return;
        }
        e.preventDefault();
    });

    window.addEventListener('resize', function () {
        if (!zoomed) return;
        // keep the image point that was in the centre there, at the new size's scale
        var c = stageCentre();
        focus.fx = (c.x - tx) / (img.naturalWidth * scale);
        focus.fy = (c.y - ty) / (img.naturalHeight * scale);
        scale = Math.max(1, fittedBox().fit * LOUPE_FACTOR);
        pinTo(c.x, c.y);
    });

    // fade the photo in once it has loaded
    function loaded() { body.classList.add('is-loaded'); }
    if (img.complete && img.naturalWidth) loaded(); else img.addEventListener('load', loaded);
})();
