
const tabledata = $(( data ));

const columndata = $(( column_options ));

const selector = ( $(( selectable )) ? [
  {
    formatter:"rowSelection",
    titleFormatter:"rowSelection",
    hozAlign:"center",
    headerSort:false,
    cellClick:function(e, cell) {
      cell.getRow().toggleSelect();
    },
    width: 20
  }
] : []);

const selectRows = function(data, rows){
  if ( $(( selectable )) ) {
    let selectedItems = document.getElementById('selected');
    selectedItems.value = data.map(a => a.id);
  }
}

var table = new Tabulator("#$(( table_id ))", {
  data: tabledata,
  printAsHtml: true,
  resizableColumns: false,
  layout: "fitColumns",
  columns: [].concat(selector, columndata),
  rowSelectionChanged: selectRows
});

