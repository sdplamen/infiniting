/*
 * Sequence editor (templates/essays/essay-sequence.html).
 *
 * Without this script the editor still works: each frame has a position
 * number. With it, the numbers are hidden and kept in sync while frames are
 * dragged by their handle (mouse, pen or touch: pointer events, so it works
 * on phones too), moved with the ↑/↓ buttons, or moved with the arrow keys
 * while the handle has focus. Nothing is saved until "Запази" is pressed.
 */
(function () {
    'use strict';

    var list = document.getElementById('sequence-list');
    var form = document.getElementById('sequence-form');
    if (!list || !form) return;

    var status = document.getElementById('sequence-status');
    var state = document.getElementById('sequence-state');
    var dirty = false;

    document.documentElement.classList.add('sequence-js');
    list.querySelectorAll('[hidden]').forEach(function (el) { el.hidden = false; });

    function items() {
        return Array.prototype.slice.call(list.children);
    }

    function markDirty() {
        if (!dirty) {
            dirty = true;
            state.textContent = 'Има незапазени промени';
            form.classList.add('is-dirty');
        }
    }

    // write the visible order into the position fields and the frame numbers
    function renumber() {
        items().forEach(function (li, i) {
            li.querySelector('.sequence-item__position-input').value = i + 1;
            li.querySelector('.sequence-item__number').textContent = i + 1;
            li.querySelector('.sequence-item__move[data-move="-1"]').disabled = i === 0;
            li.querySelector('.sequence-item__move[data-move="1"]').disabled = i === items().length - 1;
        });
    }

    function announce(li) {
        var position = items().indexOf(li) + 1;
        status.textContent = 'Кадърът е на позиция ' + position + ' от ' + items().length + '.';
    }

    function move(li, delta) {
        var siblings = items();
        var index = siblings.indexOf(li) + delta;
        if (index < 0 || index >= siblings.length) return;
        list.insertBefore(li, delta < 0 ? siblings[index] : siblings[index].nextElementSibling);
        renumber();
        markDirty();
        announce(li);
    }

    // --- buttons and keyboard -------------------------------------------------------
    list.addEventListener('click', function (e) {
        var button = e.target.closest('.sequence-item__move');
        if (!button) return;
        var li = button.closest('.sequence-item');
        move(li, Number(button.dataset.move));
        // keep focus on the same control after the move, unless it is now disabled
        (button.disabled ? li.querySelector('.sequence-item__handle') : button).focus();
    });

    list.addEventListener('keydown', function (e) {
        if (!e.target.classList.contains('sequence-item__handle')) return;
        if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
        e.preventDefault();
        var li = e.target.closest('.sequence-item');
        move(li, e.key === 'ArrowUp' ? -1 : 1);
        e.target.focus();
    });

    // --- dragging by the handle -----------------------------------------------------
    var drag = null;   // {li, pointerId, offsetY}

    list.addEventListener('pointerdown', function (e) {
        var handle = e.target.closest('.sequence-item__handle');
        if (!handle || e.button !== 0) return;
        e.preventDefault();
        var li = handle.closest('.sequence-item');
        var rect = li.getBoundingClientRect();
        drag = { li: li, pointerId: e.pointerId, offsetY: e.clientY - rect.top, startIndex: items().indexOf(li) };
        handle.setPointerCapture(e.pointerId);
        li.classList.add('is-dragging');
        list.classList.add('is-sorting');
    });

    list.addEventListener('pointermove', function (e) {
        if (!drag || e.pointerId !== drag.pointerId) return;
        // put the dragged frame before the first other frame whose middle is below the pointer
        var others = items().filter(function (li) { return li !== drag.li; });
        var before = null;
        for (var i = 0; i < others.length; i++) {
            var r = others[i].getBoundingClientRect();
            if (e.clientY < r.top + r.height / 2) { before = others[i]; break; }
        }
        if (drag.li.nextElementSibling !== before) {
            list.insertBefore(drag.li, before);
            renumber();
        }
        autoScroll(e.clientY);
    });

    function endDrag(e) {
        if (!drag || e.pointerId !== drag.pointerId) return;
        drag.li.classList.remove('is-dragging');
        list.classList.remove('is-sorting');
        if (items().indexOf(drag.li) !== drag.startIndex) {
            markDirty();
            announce(drag.li);
        }
        drag = null;
    }
    list.addEventListener('pointerup', endDrag);
    list.addEventListener('pointercancel', endDrag);

    // scroll the page when dragging near the top or bottom of the window
    function autoScroll(y) {
        var edge = 60, speed = 14;
        if (y < edge) window.scrollBy(0, -speed);
        else if (y > window.innerHeight - edge) window.scrollBy(0, speed);
    }

    // --- captions and removals also count as changes ----------------------------------
    list.addEventListener('input', markDirty);
    list.addEventListener('change', function (e) {
        if (e.target.matches('.sequence-item__remove input')) {
            e.target.closest('.sequence-item').classList.toggle('is-removed', e.target.checked);
        }
        markDirty();
    });

    form.addEventListener('submit', function () { dirty = false; });
    window.addEventListener('beforeunload', function (e) {
        if (dirty) { e.preventDefault(); e.returnValue = ''; }
    });

    renumber();
})();
