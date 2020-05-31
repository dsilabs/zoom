
$(function() {

    if( !!$.prototype.dropzone ){

        $('.field_show .images-field .dropzone').dropzone({
            url: "add-image",
            dictDefaultMessage: '',
            addRemoveLinks: false,

            init: function(){

                var field_value = this.element.attributes.field_value.nodeValue;
                var images_url = 'list-images?value=' + field_value;
                var thisDropzone = this;

                $.getJSON(images_url, function(data) {
                    $.each(data, function(index, val) {
                        var upload = { bytesSent: val.size }
                        var mockFile = {
                            name: val.name,
                            size: val.size,
                            item_id: val.item_id,
                            dataURL: val.url,
                            accepted: true
                        };

                        thisDropzone.files.push(mockFile);
                        thisDropzone.emit('addedfile', mockFile);
                        thisDropzone.createThumbnailFromUrl(
                            mockFile,
                            thisDropzone.options.thumbnailWidth,
                            thisDropzone.options.thumbnailHeight,
                            thisDropzone.options.thumbnailMethod,
                            true,
                            function(thumbnail) {
                                thisDropzone.emit('thumbnail', mockFile, thumbnail);
                            }
                        );
                        thisDropzone.emit('complete', mockFile);
                    });
                });
                thisDropzone.disable();
            }
        });

        $('.field_edit .images-field .dropzone').dropzone({
            url: 'add-image',
            dictDefaultMessage: 'drop images here or click to upload',
            dictRemoveFile: 'remove',
            dictCancelUpload: 'cancel upload',
            acceptedFiles: 'image/jpeg,image/png,image/gif',
            addRemoveLinks: true,

            init: function(){

                var field_value = this.element.attributes.field_value.nodeValue;
                var field_name = this.element.attributes.field_name.nodeValue;
                var images_url = 'list-images?value=' + field_value;
                var thisDropzone = this;

                this.on('success', function(file, item_id) {
                    file.item_id = item_id;
                });

                $.getJSON(images_url, function(data) {
                    $.each(data, function(index, val) {
                        var upload = { bytesSent: val.size }
                        var mockFile = {
                            name: val.name,
                            size: val.size,
                            item_id: val.item_id,
                            field_name: field_name,
                            dataURL: val.url,
                            accepted: true
                        };

                        thisDropzone.files.push(mockFile);
                        thisDropzone.emit('addedfile', mockFile);
                        thisDropzone.createThumbnailFromUrl(
                            mockFile,
                            thisDropzone.options.thumbnailWidth,
                            thisDropzone.options.thumbnailHeight,
                            thisDropzone.options.thumbnailMethod,
                            true,
                            function(thumbnail) {
                                thisDropzone.emit('thumbnail', mockFile, thumbnail);
                            }
                        );
                        thisDropzone.emit('complete', mockFile);
                    });
                });
            },

            sending: function(file, xhr, formData) {
                var field_name = this.element.attributes.field_name.nodeValue;
                var field_value = this.element.attributes.field_value.nodeValue;
                var csrf_token = this.element.attributes.token.nodeValue;
                console.log('sending')
                formData.append("field_name", field_name);
                formData.append("field_value", field_value);
                formData.append("csrf_token", csrf_token);
                console.log('added token')
            },

            removedfile: function(file) {
                var id = file.item_id,
                    name = file.name,
                    formData = new FormData();
                var csrf_token = this.element.attributes.token.nodeValue;
                console.log(csrf_token);
                formData.append('id', id);
                formData.append('name', encodeURIComponent(name));
                formData.append('csrf_token', csrf_token)
                $.ajax({
                    type: 'POST',
                    url: 'remove-image',
                    processData: false,
                    contentType: false,
                    // data: "id=" + id + '&name=' + encodeURIComponent(name),
                    data: formData,
                    // dataType: 'html'
                });
                var _ref;
                return (_ref = file.previewElement) != null ? _ref.parentNode.removeChild(file.previewElement) : void 0;
            },
        });
    };

});
