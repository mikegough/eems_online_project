// Initialize EEMS model if first time clicking on the model tab.
JitInitializationComplete=false;
var click_once = false;
$("#home_link").on("click", function(){
    if (! click_once) {
        $.getJSON(init_eems_file, function (results) {
            json = results;
            init(json, init_eems_file_name);
        });
    }
    click_once = true;
});


