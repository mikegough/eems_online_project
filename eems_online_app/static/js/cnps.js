// Initialize EEMS model if first time clicking on the model tab.
var click_once = false;
$("#model_link").on("click", function(){
    JitInitializationComplete=false;
    if (! click_once) {
        $.getJSON(init_eems_file, function (results) {
            json = results;
            init(json, init_eems_file_name);
        });
    }
    click_once = true;
});


