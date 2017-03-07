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

            console.log(xhr)
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
            //'epsg': epsg,
            //'extent': extent,
            'short_description': short_description,
            'long_description': long_description,
        },

        success: function (response) {
            alertify.alert("<div id='model_run_complete_alert'><img id='check_icon' src='static/img/check.png'><span id='model_run_complete_alert_text'>Upload Complete</span></div>");
        },

        error: function (xhr, errmsg, err) {
            alertify.alert("<div id='error_alert'><div id='alert_icon_div'><img id='alert_icon' src='static/img/alert.png'></div>There was an error processing your request. Please try again.</div>")
        },

        complete: function () {
            $("#spinner_div").hide()
        }
    });
}