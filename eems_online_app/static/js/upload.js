$(document).ready(function() {

    // Form validation (text based entries)
    var required_message = " This is a required field";
    $("#upload_form_text").validate({
        rules: {
            model_name: "required",
            model_author: "required",
            project: "required",
            short_description: "required",
        },
        messages: {
            model_name: required_message,
            model_author: required_message,
            project: required_message,
            short_description: required_message,
        },
        success: function(label,element) {
            label.parent().removeClass('error');
            label.remove();
        },
    });

    $('#submit').on("click", function() {
        $("label").remove();
        if (! $("#data_file").val()){
            $("#data_file").addClass('error')
        }
        if (! $("#command_file").val()){
            $("#command_file").addClass('error')
        }
        var file_form_valid = $("#file_form").valid();
        var upload_form_valid = $("#upload_form_text").valid();

        // If all form validation requirements are met, proceed to upload files.
        if (upload_form_valid && file_form_valid && $("#data_file").val() && $("#command_file").val()) {
            upload_files()
        }
    });
});

$( function() {
    $( "#creation_date" ).datepicker();
} );

$("#command_file").on('change', function(){

    $("#command_file").removeClass('error');

    var filename = $("#command_file").val();

    if (["eem", "eems", "mpt"].indexOf(filename.toLowerCase().split('.').pop()) == -1){
        $("#command_file").val('');
        alert("File must either have a .eem or .mpt file extension")
    }
});

$("#data_file").on('change', function(){

    $("#data_file").removeClass('error');

    var filename = $("#data_file").val();

    if (["nc", "zip"].indexOf(filename.toLowerCase().split('.').pop()) == -1){
        $("#data_file").val('');
        alert("File must either have a .zip or .nc file extension")
    }

    if (filename.indexOf(".zip") != -1){
        $("#spatial_resolution_row").show();
    }
    else {
        $("#spatial_resolution_row").hide();
    }

});

// Calls the view that uploads files to the server.
function upload_files(){

    // Initial notification. Files are uploading.
    alertify.alert("" +
        "<div id='upload_notifications'>" +
            "<div id='upload_status'>" +
                "<span class='status_header'>Uploading Model</span>" +
                "<img class='status_icon' id='upload_status_icon' src='../static/img/spinner.svg'>" +
                "<span class='error_text' id='upload_error_text'></span>" +
            "</div>" +
        "</div>"
        , function(){
            if (upload_process_status == 1) {
                $('#upload_form').trigger("reset");
                $('#upload_form').hide();
                $("#upload_another_file_div").show();
            }
        });

    $("#alertify-ok").hide();

    var form = document.querySelector('#file_form');
    var data = new FormData(form);

    $.ajax({
        url : "/upload_files",
        type: "POST",
        data : data,
        processData: false,
        contentType: false,
        success: function (response) {
            var json_response = JSON.parse(response);
            upload_id = json_response.upload_id;
            var error_message = json_response.error_message;
            if (typeof json_response.status != "undefined" && json_response.status == 1) {
                upload_process_status = 1;
                $("#upload_status_icon").attr("src", '../static/img/check.png');
                process_user_data(upload_id);
            }
            else {
                $("#alertify-ok").show();
                upload_process_status = 0;
                $("#upload_error_text").html("<div id='upload_status_text'>" + error_message + "<p><b>Upload ID: </b>" + upload_id + "</div>");
                $("#upload_status_icon").attr("src", '../static/img/error.png');
            }

        },
        error: function (xhr, errmsg, err) {

            $("#spinner_div").hide();
            console.log(xhr);
            console.log(errmsg);
            console.log(err);
            upload_process_status = 0;
            $("#upload_error_text").html("<div id='upload_status_text'>" + "There was an error uploading your files. Please try again later, or contact support.<br>" + xhr.responseText.split("Request Method")[0].replace("\n","<br>") + "<p><b>Upload ID: </b>" + upload_id +"</div>");
            $("#upload_status_icon").attr("src", '../static/img/error.png');
        },
    });
}

// Calls the upload_form view, which basically just hands this information off to the celery worker to run EEMS.
function process_user_data(upload_id) {

    $("#upload_notifications").append(
        "<div id='processing_status'>" +
        "<span class='status_header'>Processing Model</span>" +
        "<img class='status_icon' id='processing_status_icon' src='../static/img/spinner.svg'>" +
        "<span class='error_text' id='processing_error_text'></span>" +
        "</div>"
    );

    //$("#spinner_text").html("Processing data...");

    var username = $("#username").text();
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
            'model_name': model_name,
            'model_author': model_author,
            'creation_date': creation_date,
            'resolution': resolution,
            'project':project,
            //'epsg': epsg,
            //'extent': extent,
            'short_description': short_description,
            'long_description': long_description,
            'username':username

        },

        success: function (response) {
            //$("#upload_form").hide();
            check_eems_status(upload_id);
        },

        error: function (xhr, errmsg, err) {
            alertify.alert("<div id='error_alert'><div id='alert_icon_div'><img id='alert_icon' src='../static/img/alert.png'></div>There was an error processing your request. Please try again.</div>")
        },

    });

}

// Poll the server to check the status of the EEMS model run.
function check_eems_status(upload_id) {

    $.ajax({
        url: "/check_eems_status", // the endpoint
        type: "POST", // http method
        data: {
            'upload_id': upload_id,
        },

        complete: function (response) {
            responseText = JSON.parse(response.responseText)

            if (responseText.status == null) {
                console.log("Checking upload status");
                setTimeout('check_eems_status(upload_id)', 5000);
            }
            else if (responseText.status == "1") {
                $("#alertify-ok").show();
                upload_process_status = 1;
                $("#processing_status_icon").attr("src", '../static/img/check.png');
            }
            else {
                $("#alertify-ok").show();
                upload_process_status = 0;
                $("#processing_error_text").html("<div id='upload_status_text'>" + responseText.error_message + "<p><b>Upload ID: </b>" + upload_id +"</div>");
                $("#processing_status_icon").attr("src", '../static/img/error.png');
            }

        },

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

$("#logout_button").on("click", function()
    {
        window.location.replace("logout")

    }
);

$("#go_to_eems_online_button").on("click", function()
    {
        window.location = "/"

    }
);

$("#go_to_admin_page_button").on("click", function()
    {
        window.location = "/admin"

    }
);
