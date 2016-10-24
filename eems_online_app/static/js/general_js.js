$( document ).ready(function() {
    $("#files").prop('value', '');
    init();
});

$("#run_eems_button").click(function(){run_eems()})

function run_eems() {

    eems_operator_changes_string = JSON.stringify(eems_operator_changes)

    $.ajax({
        url: "", // the endpoint
        type: "POST", // http method
        data: {
            'eems_operator_changes_string':eems_operator_changes_string
        },

        // handle a successful response
        success: function (json) {
            results = JSON.parse(json)
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                " <a href='#' class='close'>&times;</a></div>");
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

