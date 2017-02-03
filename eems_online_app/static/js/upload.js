$( function() {
    $( "#date" ).datepicker();
} );

function promptForPassword() {
    alertify.prompt("Enter the password", function (e, str) {
        if (e) {
            $.ajax({

                url: "/check_pass", // the endpoint
                type: "POST", // http method
                data: {
                    'user_pass': str,
                },

                success: function (response) {
                    if (response == "yes") {
                        $("#upload_form").show()
                    }
                    else {
                        alertify.alert("Invalid Password. Please try again.", function () { promptForPassword()});
                    }
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr)
                }
            });

        }
        else {
              document.location.href="/";
        }
    });
    $('#alertify-text').attr('type','password');
}

promptForPassword();

$("#submit").click(function(e) {

    $("#spinner_div").show();

    var owner = $("#owner").val();
    var model_name = $("#model_name").val();
    var model_author = $("#model_author").val();
    var creation_date = $("#creation_date").val();

    var xmin = $("#xmin").val();
    var ymin = $("#ymin").val();
    var xmax = $("#xmax").val();
    var ymax = $("#ymax").val();

    var extent = "[[" + xmin +  "," + ymin + "],["  + xmax + "," + ymax + "]]";
    var short_description = $("#short_description").val();
    var long_description = $("#long_description").val();

    $.ajax({
        url: "/upload_submit", // the endpoint
        type: "POST", // http method
        data: {
            'owner': owner,
            'model_name': model_name,
            'model_author': model_author,
            'creation_date': creation_date,
            'extent': extent,
            'short_description': short_description,
            'long_description': long_description,
        },

        success: function (response) {
            alertify.alert("<div id='model_run_complete_alert'><img id='check_icon' src='static/img/check.png'><span id='model_run_complete_alert_text'>Upload Complete</span></div>");
        },

        error: function (xhr, errmsg, err) {
            alertify.alert("<div id='error_alert'><div id='alert_icon_div'><img id='alert_icon' src='static/img/alert.png'></div>There was an error processing your request. Please try again.</div>")
        },

        complete: function(){
            $("#spinner_div").hide()
        }
    });
});