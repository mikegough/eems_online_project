// Only show the Download Button for approved users.
$( document ).ready(function() {
    if ((["sam.young", "mike.gough"]).indexOf(eems_user) == -1) {
        $("#download_label").addClass("permanently_disabled");
    }
});

// If a user accesses the model through a model link
if (initial_tab == "model"){
    $("#home_link").removeClass("active");
    $("#model_link").addClass("active");
    $("#model").show();
    $("#home").hide();
}

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


