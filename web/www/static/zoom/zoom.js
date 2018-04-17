

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


        if ( $('.chosen').length > 0 ) { $('.chosen').chosen({search_contains: true}); };

        $('.flag').click(toggle_flag);

    });
