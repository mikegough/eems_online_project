$("#submit").click(function(e) {

    var name = $("#name").val();
    var xmin = $("#xmin").val();
    var ymin = $("#ymin").val();
    var xmax = $("#xmax").val();
    var ymax = $("#ymax").val();

    var extent = "[[" + xmin +  "," + ymin + "],["  + xmax + "," + ymax + "]]";
    var short_description = $("#short_description").val();
    var long_description = $("#long_description").val();
    var owner = $("#owner").val();

    $.ajax({
        url: "/upload_submit", // the endpoint
        type: "POST", // http method
        data: {
            'name': name,
            'extent': extent,
            'short_description': short_description,
            'long_description': long_description,
            'owner': owner,
        },

        // handle a successful response
        success: function (response) {
            alertify.alert("Upload complete");
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
        }
    });
});