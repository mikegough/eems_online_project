$( function() {
    $( "#creation_date" ).datepicker();
} );

$("#submit").click(function(e) {

    upload_files()

});

$("#data_file").on('change', function(){

    var filename = $('input[type=file]').val();

    if (filename.indexOf(".zip") != -1){
        $("#spatial_resolution_row").show();
    }
    else {
        $("#spatial_resolution_row").hide();
    }

});

function upload_files(){

    $("#spinner_div").show();

    $("#spinner_text").html("Uploading Files...");

    var form = document.querySelector('#file_form');
    var data = new FormData(form);

    $.ajax({
        url : "/upload_files",
        type: "POST",
        data : data,
        processData: false,
        contentType: false,
        success:function(response){

           upload_id = response

           process_user_data(upload_id)

        },
        error: function (xhr, errmsg, err) {

            $("#spinner_div").hide();
            console.log(xhr);
            console.log(errmsg);
            console.log(err);
            alertify.alert("<div id='error_alert'><div id='alert_icon_div'><img id='alert_icon' src='static/img/alert.png'></div>There was an error processing your request. Check to make sure that your EEMS command file is valid and free of errors.</div>")
        }
    });

}

function process_user_data(upload_id) {

    $("#spinner_text").html("Processing data...");

    var owner = username;
    var model_name = $("#model_name").val();
    var model_author = $("#model_author").val();
    var creation_date = $("#creation_date").val();
    var resolution = $("#resolution").val();
    var project = $("#project").val();

    /* May need to keep for manual coordinate entry override.
     var xmin = $("#xmin").val().replace(/\s+/g, '');
     var ymin = $("#ymin").val().replace(/\s+/g, '');
     var xmax = $("#xmax").val().replace(/\s+/g, '');
     var ymax = $("#ymax").val().replace(/\s+/g, '');

     var epsg = $("#epsg").val();
     var extent = "[[" + ymin +  "," + xmin + "],["  + ymax + "," + xmax + "]]";
    */
    var short_description = $("#short_description").val();
    var long_description = $("#long_description").val();

    $.ajax({
        url: "/upload_form", // the endpoint
        type: "POST", // http method
        data: {
            'upload_id': upload_id,
            'owner': owner,
            'model_name': model_name,
            'model_author': model_author,
            'creation_date': creation_date,
            'resolution': resolution,
            'project':project,
            //'epsg': epsg,
            //'extent': extent,
            'short_description': short_description,
            'long_description': long_description,
        },

        success: function (response) {
            alertify.alert("<div id='model_run_complete_alert'><img id='check_icon' src='static/img/check.png'><span id='model_run_complete_alert_text'>Your model has been received and is being processed. This may take several minutes. When complete, your model will be accessible through EEMS Online. <p>You may now close this browser tab or upload another model.</span></div>", function(){
                $('#upload_form').trigger("reset");
                $("#upload_another_file_div").show();
            });
            $("#upload_form").hide();
        },

        error: function (xhr, errmsg, err) {
            alertify.alert("<div id='error_alert'><div id='alert_icon_div'><img id='alert_icon' src='static/img/alert.png'></div>There was an error processing your request. Please try again.</div>")
        },

        complete: function () {
            $("#spinner_div").hide()
        }
    });
}

$("#upload_another_file_button").on("click", function(){
    // Reset form elements
    $("#spatial_resolution_row").hide();
    $("#upload_form").find("input").val("");
    $("#short_description").val("");
    $("#long_description").val("");
    $('#submit').val('Submit');

    $("#upload_form").show();
    $("#upload_another_file_div").hide();
});
