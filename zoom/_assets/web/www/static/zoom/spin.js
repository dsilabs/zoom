//
// spin.js wrapper for Zoom
//

    $(function() {

        var pb_target = document.getElementById('spinner');
        if (pb_target) {
            var opts = {
              lines: 9, // The number of lines to draw
              length: 11, // The length of each line
              width: 4, // The line thickness
              radius: 6, // The radius of the inner circle
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
