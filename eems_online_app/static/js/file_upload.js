$('input:file').change(
    function(e){
        var filename=e.target.files[0].name
        $("#current_file").html("<b>Current Model:</b> " + filename.replace('.json','').replace('.JSON',''))
        var startByte = e.target.getAttribute('data-startbyte');
        var endByte = e.target.getAttribute('data-endbyte');
        readBlob(startByte, endByte);
    }
);

function readBlob(opt_startByte, opt_stopByte) {

    var files = document.getElementById('files').files;
    if (!files.length) {
      alert('Please select a file!');
      return;
    }

    var file = files[0];
    var start = parseInt(opt_startByte) || 0;
    var stop = parseInt(opt_stopByte) || file.size - 1;

    var reader = new FileReader();

    // If we use onloadend, we need to check the readyState.
    reader.onloadend = function(evt) {
      if (evt.target.readyState == FileReader.DONE) { // DONE == 2
        json_string = JSON.stringify(eval("(" + evt.target.result + ")"));
        json = JSON.parse(json_string);
        $("#infovis").empty()
        init()
      }
    };

    var blob = file.slice(start, stop + 1);
    reader.readAsBinaryString(blob);
}

jQuery("input#files").change(function () {
   //alert(jQuery(this).val())
});


