window.addEventListener('load', function() {
    var container = document.getElementById('files-manager'),
        form = document.getElementById('--fm-upload-form');

    //  Ensure we're in edit mode.
    if (container.getAttribute('data-mode') != 'edit') return;

    //  Retrieve more relevant elements.
    var area = document.getElementById('--fm-drop-area'),
        field = document.getElementById('--fm-upload-field'),
        label = document.getElementById('--fm-upload-label');

    //  Show the upload area.
    area.removeAttribute('style');
    var defaultLabelValue = label.innerHTML;

    //	Define some helpers.
    /**
    *   Submit a form containing the given content to the destination URL, invoking
    *   the success callback if the response isn't obviously an error.
    */
    function submitForm(destination, content, success) {
        //	Copy CSRF token.
        content.csrf_token = document.getElementById('--fm-csrf').value;

        //  Generate the form data object from the supplied key, value content map.
        var data = new FormData();
        var keys = Object.keys(content);
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i], value = content[key];
            if (value instanceof Array) data.append(key, value[0], value[1]);
            else data.append(key, value);
        }

        //  Create and dispatch an XHR of the form submission.
        var xhr = new XMLHttpRequest();
        xhr.open('POST', destination);
        xhr.addEventListener('readystatechange', () => {
            if (xhr.readyState != 4) return;
            if (xhr.status >= 400) return;
            success(xhr.status);
        });
        xhr.send(data);
    }

    /**
    *   Handle a file being selected for upload by reading it, submitting it to the
    *   server, then either calling next or reloading the page so the changes are
    *   visible. 
    */
    function handleFileSelection(file, next) {
        resetDragCosmetics();

        //  Check for I.E. 9-.
        if (!('FileReader' in window)) {
            window.alert('Please use a newer browser');
            return;
        }

        //  Read the file and submit it as a form.
        var reader = new FileReader();
        reader.addEventListener('load', function() {
            submitForm(form.action, {
                file: [new Blob([reader.result], {type: file.type}), file.name],
                mimetype: file.type
            }, function (status) {
                if (status == 201) {
                    if (next) next();
                    else window.location.reload();
                }
            });
        });
        reader.readAsArrayBuffer(file);
    }

    /**
    *   Dispatch the file selection handler for each element in the given list. 
    */
    function dispatchFileSelectionHandler(fileList, i) {
        var then = (i == fileList.length - 1) ? null : (function() {
            dispatchFileSelectionHandler(fileList, i + 1);
        });

        handleFileSelection(fileList[i], then);
    }

    /**
    *   Reset the look of the file drop area. 
    */
    function resetDragCosmetics() {
        container.removeAttribute('data-fm-drag');
        label.innerHTML = defaultLabelValue;
    }

    //  Clicking anywhere on the upload area should show the selector.
    area.addEventListener('click', function(event) {
        event.stopPropagation();

        label.click();
    });

    //  Accept drag events containing files.
    area.addEventListener('dragover', function(event) {
        var item = event.dataTransfer.items[0];
        if (item.kind != 'file') return;

        event.preventDefault();
        event.stopPropagation();
    });

    //  Update cosmetics based on an accepted drag event ticking.
    area.addEventListener('dragenter', function(event) {
        event.preventDefault();

        container.setAttribute('data-fm-drag', 'true');
        label.innerHTML = '<strong>Drop to add</strong>';
    });
    //  Clear cosmetics on a drag event ending.
    area.addEventListener('dragleave', resetDragCosmetics);

    //  Accept drop events by uploading all files in the data transfer.
    area.addEventListener('drop', function(event) {
        event.preventDefault();
        event.stopPropagation();

        dispatchFileSelectionHandler(event.dataTransfer.files, 0);
    });
    //  Accept direct selection by uploading all files.
    field.addEventListener('change', function() {
        dispatchFileSelectionHandler(field.files, 0);
    });

    //	Set up delete buttons.
    function setupButton(button) {
        button.addEventListener('click', function() {
            submitForm('/content/files/delete', {
                file_id: button.id,
            }, function() {
                var cur = button;
                while (cur.className != '--fm-file-item') {
                    cur = cur.parentElement;
                }

                cur.setAttribute('style', 'display: none;');
            });
        });
    }

    var deleteButtons = document.getElementsByClassName('--fm-delete');
    for (var i = 0; i < deleteButtons.length; i++) {
        setupButton(deleteButtons[i]);
    }
});
