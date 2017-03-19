
    function toggle_flag(){
        var label = $(this).attr('label'),
            icon = $(this).attr('icon'),
            url = $(this).attr('url');
        $.post('/flags/toggle', {'LABEL': label, 'URL': url, 'ICON': icon } );
        $(this).toggleClass(icon+'_on');
    }

    $(function() {

        $('.date_field').datepicker({
            dateFormat: 'M d, yy',
            changeMonth: true,
            changeYear: true
        });

        $('.birthdate_field').datepicker({ dateFormat: 'M d, yy', changeMonth: true, changeYear: true, yearRange: '-120:+00' });

        if( !!$.prototype.dropzone ){
            $('.field_show div.images_field').dropzone({
                url: "add_image",
                dictDefaultMessage: '',
                addRemoveLinks: false,
                init: function(){
                    var field_value = this.element.attributes.field_value.nodeValue;
                    var base_url = this.element.attributes.url.nodeValue;
                    var images_url = base_url + 'list_images?value=' + field_value;
                    var thisDropzone = this;

                    $.getJSON(images_url, function(data) {
                        $.each(data, function(index, val) {
                            var upload = { bytesSent: val.size }
                            var mockFile = { name: val.name, size: val.size, item_id: val.item_id, accepted: true };

                            thisDropzone.files.push(mockFile);
                            thisDropzone.emit('addedfile', mockFile);
                            thisDropzone.createThumbnailFromUrl(mockFile, val.url);
                            thisDropzone.emit('complete', mockFile);
                        });
                    });
                    thisDropzone.disable();
                }
            });

            $('.field_edit div.images_field').dropzone({
                url: "add_image",
                dictDefaultMessage: 'drop images here or click to upload',
                dictRemoveFile: 'remove',
                dictCancelUpload: 'cancel upload',
                acceptedFiles: 'image/jpeg,image/png,image/gif',
                addRemoveLinks: true,
                removedfile: function(file) {
                    var id = file.item_id,
                        name = file.name;
                    $.ajax({
                        type: 'POST',
                        url: 'remove_image',
                        data: "id=" + id + '&name=' + encodeURIComponent(name),
                        dataType: 'html'
                    });
                    var _ref;
                    return (_ref = file.previewElement) != null ? _ref.parentNode.removeChild(file.previewElement) : void 0;
                },
                sending: function(file, xhr, formData) {
                    var field_name = this.element.attributes.field_name.nodeValue;
                    var field_value = this.element.attributes.field_value.nodeValue;
                    formData.append("field_name", field_name);
                    formData.append("field_value", field_value);
                    console.log(file);
                    console.log(formData);
                },
                init: function(){
                    var field_value = this.element.attributes.field_value.nodeValue;
                    var field_name = this.element.attributes.field_name.nodeValue;
                    var images_url = 'list_images?value=' + field_value;
                    var thisDropzone = this;

                    this.on('success', function(file, item_id) {
                        file.item_id = item_id;
                    });

                    $.getJSON(images_url, function(data) {
                        $.each(data, function(index, val) {
                            var upload = { bytesSent: val.size }
                            var mockFile = { name: val.name, size: val.size, item_id: val.item_id, field_name: field_name, accepted: true };

                            thisDropzone.files.push(mockFile);
                            thisDropzone.emit('addedfile', mockFile);
                            thisDropzone.createThumbnailFromUrl(mockFile, val.url);
                            thisDropzone.emit('complete', mockFile);
                        });
                    });
                }
            });
        };

        if ( $('.chosen').length > 0 ) { $('.chosen').chosen({search_contains: true}); };

        $('.flag').click(toggle_flag);

        var pb_target = document.getElementById('spinner');
        if (pb_target) {
            var opts = {
              lines: 9, // The number of lines to draw
              length: 11, // The length of each line
              width: 4, // The line thickness
              radius: 12, // The radius of the inner circle
              corners: 1, // Corner roundness (0..1)
              rotate: 0, // The rotation offset
              color: '#000', // #rgb or #rrggbb
              speed: 1, // Rounds per second
              trail: 60, // Afterglow percentage
              shadow: false, // Whether to render a shadow
              hwaccel: false, // Whether to use hardware acceleration
              className: 'spinner', // The CSS class to assign to the spinner
              zIndex: 2e9, // The z-index (defaults to 2000000000)
              top: 'auto', // Top position relative to parent in px
              left: 'auto' // Left position relative to parent in px
            };
           var spinner = new Spinner(opts).spin(pb_target);
        };

    });
