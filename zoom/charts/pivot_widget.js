$(function(){
    var derivers = $.pivotUtilities.derivers;
    var renderers = $.extend(
        $.pivotUtilities.renderers,
        $.pivotUtilities.c3_renderers,
        $.pivotUtilities.d3_renderers,
        $.pivotUtilities.export_renderers
        );

    $("#$(( chart.selector ))").pivotUI( $(( chart.data )), {
        rows: $((chart.rows)),
        cols: $((chart.columns)),
        vals: $((chart.values)),
        rowOrder: "$((chart.row_order))",
        colOrder: "$((chart.col_order))",
        showUI: $((chart.show_ui)),
        aggregators: $.pivotUtilities.aggregators,
        aggregatorName: "$((chart.aggregator_name))",        
        rendererName: "$((chart.renderer_name))",
    
    });
});