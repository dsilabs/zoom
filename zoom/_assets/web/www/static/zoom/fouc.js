$(function() {
    // FOUC
    $(".nojs").css("display", "block");
    $(".inojs").css("display", "inline");
    if ('sparkline_display_visible' in $) {
        $.sparkline_display_visible();
    }
});
