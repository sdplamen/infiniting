/*
 * Direct photo upload (photo create/edit forms; server side in photos/direct_upload.py).
 *
 * As soon as a file is picked: Django signs the upload, the browser sends the
 * file straight to Cloudinary with a progress bar and a preview, and the
 * caption can be written meanwhile. The form then submits only the uploaded
 * file's reference and its first 64 KB (for EXIF), so publishing is instant.
 * Pressing the button mid-upload publishes as soon as the upload finishes.
 *
 * If signing or the upload fails, the file input keeps its name and the form
 * uploads the file the normal way. Without JavaScript nothing here runs.
 */
(function () {
    'use strict';

    var form = document.querySelector('form[data-direct-upload-form]');
    var input = form && form.querySelector('input[type=file][data-direct-upload]');
    if (!input || !window.FormData || !window.XMLHttpRequest || !window.fetch) return;

    var EXIF_HEAD_BYTES = 64 * 1024;
    var DIRECT_FIELDS = ['direct_public_id', 'direct_version', 'direct_format', 'direct_signature', 'exif_head'];
    var fileFieldName = input.name;
    var submit = form.querySelector('[type=submit]');
    var submitHTML = submit ? submit.innerHTML : '';
    var csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;

    var state = 'idle';            // idle | uploading | done | failed
    var request = null;
    var publishWhenDone = false;
    var previewURL = null;

    // --- status box under the file input ----------------------------------------
    var box = document.createElement('div');
    box.className = 'direct-upload';
    box.hidden = true;
    box.innerHTML =
        '<img class="direct-upload__preview" alt="">' +
        '<div class="direct-upload__body">' +
        '  <div class="direct-upload__bar" role="progressbar" aria-label="Качване" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div>' +
        '  <p class="direct-upload__status" aria-live="polite"></p>' +
        '</div>';
    input.insertAdjacentElement('afterend', box);
    var bar = box.querySelector('.direct-upload__bar');
    var status = box.querySelector('.direct-upload__status');

    function field(name) { return form.querySelector('[name="' + name + '"]'); }

    function setProgress(fraction) {
        var pct = Math.round(fraction * 100);
        bar.firstElementChild.style.width = pct + '%';
        bar.setAttribute('aria-valuenow', pct);
    }

    function show(kind, text) {
        box.hidden = false;
        box.className = 'direct-upload is-' + kind;
        status.textContent = text;
    }

    function clearDirect() {
        DIRECT_FIELDS.forEach(function (name) { var f = field(name); if (f) f.value = ''; });
    }

    function restoreButton() {
        if (!submit) return;
        submit.disabled = false;
        submit.innerHTML = submitHTML;
    }

    // signing or uploading failed: send the file with the form instead
    function fallBack(reason) {
        state = 'failed';
        clearDirect();
        input.name = fileFieldName;
        show('failed', reason + ' Снимката ще се качи заедно с формата.');
        restoreButton();
        if (publishWhenDone) form.submit();
    }

    function toBase64(buffer) {
        var bytes = new Uint8Array(buffer), text = '';
        for (var i = 0; i < bytes.length; i += 0x8000) {
            text += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
        }
        return btoa(text);
    }

    function start(file) {
        if (request) request.abort();
        clearDirect();
        input.name = fileFieldName;
        publishWhenDone = false;
        restoreButton();
        state = 'uploading';
        setProgress(0);

        if (previewURL) URL.revokeObjectURL(previewURL);
        previewURL = URL.createObjectURL(file);
        box.querySelector('.direct-upload__preview').src = previewURL;
        show('uploading', 'Качване… можете да пишете описанието междувременно.');

        var signed = fetch(form.dataset.signUrl, {
            method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': csrf },
        }).then(function (response) {
            if (!response.ok) throw new Error('sign ' + response.status);
            return response.json();
        });
        var head = file.slice(0, EXIF_HEAD_BYTES).arrayBuffer().then(toBase64);

        Promise.all([signed, head]).then(function (results) {
            var sig = results[0], headBase64 = results[1];
            var data = new FormData();
            data.append('file', file);
            ['api_key', 'timestamp', 'signature', 'folder', 'allowed_formats'].forEach(function (key) {
                data.append(key, sig[key]);
            });

            var xhr = request = new XMLHttpRequest();
            xhr.open('POST', sig.upload_url);
            xhr.upload.addEventListener('progress', function (e) {
                if (e.lengthComputable) setProgress(e.loaded / e.total);
            });
            xhr.addEventListener('load', function () {
                if (xhr !== request) return;               // a newer file was picked meanwhile
                var result = {};
                try { result = JSON.parse(xhr.responseText); } catch (err) { /* handled below */ }
                if (xhr.status !== 200 || !result.public_id) {
                    fallBack((result.error && result.error.message ? result.error.message + '.' : 'Качването не успя.'));
                    return;
                }
                field('direct_public_id').value = result.public_id;
                field('direct_version').value = result.version;
                field('direct_format').value = result.format;
                field('direct_signature').value = result.signature;
                field('exif_head').value = headBase64;
                input.removeAttribute('name');             // don't send the file a second time
                state = 'done';
                setProgress(1);
                show('done', 'Качена. Остава само да публикувате.');
                if (publishWhenDone) form.submit();
            });
            xhr.addEventListener('error', function () {
                if (xhr === request) fallBack('Връзката с Cloudinary прекъсна.');
            });
            xhr.send(data);
        }).catch(function () {
            fallBack('Директното качване не е достъпно.');
        });
    }

    input.addEventListener('change', function () {
        if (input.files && input.files[0]) {
            start(input.files[0]);
        } else {
            if (request) request.abort();
            state = 'idle';
            clearDirect();
            input.name = fileFieldName;
            box.hidden = true;
        }
    });

    // pressed "upload" before the file finished: publish as soon as it has
    form.addEventListener('submit', function (e) {
        if (state !== 'uploading') return;
        e.preventDefault();
        publishWhenDone = true;
        if (submit) {
            submit.disabled = true;
            submit.innerHTML = 'Публикува се след качването…';
        }
    });
})();
