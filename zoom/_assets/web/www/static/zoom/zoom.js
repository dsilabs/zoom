

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


//  Flag management.
$(function() {
    function dispatchToggle(id) {
        $.ajax({
            method: 'PUT',
            url: '/_zoom/flags',
            data: {id: id}
        });
    }

    function toggleFlag(event, flag) {
        event.stopPropagation();
        event.preventDefault();
        var newState = flag.attr('data-state') == 'true' ? 'false' : 'true';
        
        dispatchToggle(flag.attr('data-flag-id'));

        flag.attr('data-state', newState);
        flag.find('[data-flag-case]').each(function() {
            var flagCase = $(this);
            flagCase.attr('style', flagCase.attr('data-flag-case') == newState ? '' : 'display: none');
        });
    };

    $('[data-flag-id]').each(function() {
        var flag = $(this);

        flag.on('click', function(event) { toggleFlag(event, flag); });
    });
});
