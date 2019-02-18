// Initialize EEMS model if first time clicking on the model tab.
JitInitializationComplete=true
var click_once = false;
$("#home").hide();
$("#home_link").on("click", function(){
    if (! click_once) {
        $.getJSON(init_eems_file, function (results) {
            json = results;
            init(json, init_eems_file_name);
        });
    }
    click_once = true;
});


