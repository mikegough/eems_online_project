function readBlob(opt_startByte, opt_stopByte, filename) {

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
        if  (filename.indexOf(".json") >= 0)
          {
              var json_string = JSON.stringify(eval("(" + evt.target.result + ")"));
              var json = JSON.parse(json_string);
              init(json,filename)
          }
       else if  (filename.indexOf(".eem") >= 0)
          {
              var eems_file_contents = evt.target.result;
              $("#infovis").empty()
              load_eems_user_model(filename, eems_file_contents)
          }
      }
    };

    var blob = file.slice(start, stop + 1);
    reader.readAsBinaryString(blob);
}

jQuery("input#files").change(function () {
   //alert(jQuery(this).val())
});


