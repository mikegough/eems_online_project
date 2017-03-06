$( function() {
    $( "#creation_date" ).datepicker();
} );

$("#submit").click(function(e) {

    upload_files()
    //process_user_data()

});

function upload_files(){

    $("#spinner_div").show();

    var form = document.querySelector('#file-form');
    var data = new FormData(form);

    $.ajax({
        url : "/upload_files",
        type: "POST",
        data : data,
        processData: false,
        contentType: false,
        success:function(response){

            process_user_data()
        },
        error: function (xhr, errmsg, err) {
            //if fails
            console.log(xhr)
        }
    });

}

function process_user_data() {


    var owner = $("#owner").val();
    var model_name = $("#model_name").val();
    var model_author = $("#model_author").val();
    var creation_date = $("#creation_date").val();
    var resolution = $("#resolution").val();

    /*
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