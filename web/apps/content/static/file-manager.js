window.addEventListener('load', function() {
    var container = document.getElementById('files-manager'),
        form = document.getElementById('--fm-upload-form');

    if (!form) return; // Not in edit mode.

    //	Define some helpers.
    function submitForm(destination, content, success) {
        //	Copy CSRF token.
        content.csrf_token = document.getElementById('--fm-csrf').value;

        var data = new FormData();
        var keys = Object.keys(content);
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i], value = content[key];
            if (value instanceof Array) data.append(key, value[0], value[1]);
            else data.append(key, value);
        }

        var xhr = new XMLHttpRequest();
        xhr.open('POST', destination);
        xhr.addEventListener('readystatechange', () => {
            if (xhr.readyState != 4) return;
            if (xhr.status >= 400) return;
            success(xhr.status);
        });
        xhr.send(data);
    }

    //	Set up drag and drop.
    var area = document.getElementById('--fm-drop-area'),
        field = document.getElementById('--fm-upload-field'),
        label = document.getElementById('--fm-upload-label');

    area.removeAttribute('style');
    var defaultLabelValue = label.innerHTML;

    area.addEventListener('click', function(event) {
        event.stopPropagation();

        label.click();
    });

    function handleFileSelection(file) {
        resetDragCosmetics();

        if (!('FileReader' in window)) {
            window.alert('Please use a newer browser');
        }

        var reader = new FileReader();
        reader.addEventListener('load', function() {
            submitForm(form.action, {
                file: [new Blob([reader.result], {type: file.type}), file.name],
                mimetype: file.type
            }, function (status) {
                if (status == 201) window.location.reload();
            });
        });
        reader.readAsArrayBuffer(file);
    }

    function resetDragCosmetics() {
        container.removeAttribute('data-fm-drag');
        label.innerHTML = defaultLabelValue;
    }

    area.addEventListener('dragover', function(event) {
        var item = event.dataTransfer.items[0];
        if (item.kind != 'file') return;

        event.preventDefault();
        event.stopPropagation();
    });

    area.addEventListener('dragenter', function(event) {
        event.preventDefault();

        container.setAttribute('data-fm-drag', 'true');
        label.innerHTML = '<strong>Drop to add</strong>';
    });

    area.addEventListener('dragleave', resetDragCosmetics);

    area.addEventListener('drop', function(event) {
        event.preventDefault();
        event.stopPropagation();

        handleFileSelection(event.dataTransfer.files[0]);
    });

    field.addEventListener('change', function() {
        handleFileSelection(field.files[0]);
    });

    //	Setup up delete buttons.
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
