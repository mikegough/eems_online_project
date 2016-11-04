$( document ).ready(function() {

    $("#files").prop('value', '');

    // Set the eems model dropdown menu to the first option on page load.
    $("#eems_model_dropdown").val($("#eems_model_dropdown option:first").val());
});



$.get(eems_file, function(results) {
    json=JSON.parse(results)
    $("#infovis").empty()
    init(json)
});

$("#run_eems_button").click(function(){run_eems(eems_model)});
$("#modify_eems_button").click(function(){modify_eems()});

function load_eems(eems_filename, eems_file_contents) {

    alert(eems_file_contents)

    $.ajax({
        url: "/load_eems", // the endpoint
        type: "POST", // http method
        data: {
            'eems_filename': eems_filename,
            'eems_file_contents': eems_file_contents
        },

        // handle a successful response
        success: function (json) {
            //results = JSON.parse(json)
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

function run_eems() {

    eems_operator_changes_string = JSON.stringify(eems_operator_changes)

    $.ajax({
        url: "/run_eems", // the endpoint
        type: "POST", // http method
        data: {
            'eems_model': eems_model,
            'eems_operator_changes_string': eems_operator_changes_string
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


function changeEEMSOperator(node_id, alias, node_current_operator, children_string) {

    var children_array = children_string.split(',');

    if (node_current_operator ==  "Convert to Fuzzy"){

        alertify.confirm(
            "<div id='change_operator_form'><b>Node: </b>" + alias +
            "<p><b>True Threshold: </b> <input id='true_threshold' type='text' size='6'>" +
            "<p><b>False Threshold: </b> <input id='false_threshold' type='text' size='6'>" +
            "</div>"
            , function (e, str) {
                if (e) {
                    var true_threshold = $("#true_threshold").val();
                    var false_threshold = $("#false_threshold").val();
                    updateEEMSThresholds(node_id, alias, true_threshold,false_threshold);
                }
            }
        )

    }

    // Non-Fuzzy Operations
    else if (["Difference", "Weighted Sum"].includes(node_current_operator)){
        alertify.confirm(
            "<div id='change_operator_form'><b>Node: </b>" + alias +
            "<p><b>Operator: </b>" +
            "<select id='new_operator_select'>" +
                "<option name='new_operator' value='Difference'>Difference</option>" +
                "<option name='new_operator' value='Weighted Sum'>Weighted Sum</option>" +
            "</select>" +
            "</div>"
            // On Confirm
            , function (e, str) {
                if (e) {
                    var new_operator = $("#new_operator_select option:selected").text();
                    updateEEMSOperator(node_id, alias, new_operator);
                }
            }
        );
    }

    // Fuzzy Operations
    else {
        alertify.confirm(
            "<div id='change_operator_form'><b>Node: </b>" + alias +
            "<p><b>Operator: </b>" +
                "<select id='new_operator_select'>" +
                    "<option name='new_operator' value='And'>And</option>" +
                    "<option name='new_operator' value='Or'>Or</option>" +
                    "<option name='new_operator' value='Negative Or'>Negative Or</option>" +
                    "<option name='new_operator' value='Union'>Union</option>" +
                    "<option name='new_operator' value='Selected Union'>Selected Union</option>" +
                    "<option name='new_operator' value='Weighted Union'>Weighted Union</option>" +
                "</select>" +
            "<div id='operator_options'></div>" +
            "</div>"

            // On Confirm...
            , function (e, str) {
                if (e) {
                    var new_operator = $("#new_operator_select option:selected").text();

                    // Get options
                    var options={};

                    var new_operator = $("#new_operator_select").val();

                    if (new_operator == "Weighted Union") {

                        $('#options *').filter(':selected').each(function (a, b) {
                            options["truest_or_falsest"] = b.value
                        });
                    }

                    else if (new_operator == "Selected Union") {

                        $('#options *').filter(':input').each(function (a, b) {
                            options[b.name] = b.value
                        });
                    }

                    // Call function to store new eems operator and options in a dictionary
                    updateEEMSOperator(node_id, alias, new_operator, options)
                }
            }
        );
    }

    // Operator specific options
    $("#new_operator_select").on("change", function(){

        var new_operator=this.value;

        $("#operator_options").empty();

        switch(new_operator) {

            case "Weighted Union":

                // Create the options form.
                $("#operator_options").append("<form id='options'>");
                $("#options").append("<table id='weighted_union_table'>");

                // Iterate over each child and create an input weighted union field.
                $.each(children_array, function(index,child){

                    $("#weighted_union_table").append("<tr><td>" +child + "</td><td><input type='text' name='" + child + "' size=3></td></tr>")

                });
                $("#options").append("</table>");
                $("#operator_options").append("</form>");
                break;

            case "Selected Union":

                // Create the options form.
                $("#operator_options").append("<form id='options'>");

                $("#options").append("<b>Select the: </b>");

                $("#options").append(
                    "<select>" +
                    "<option name='truest_or_falsest' value='t'>Truest</option>" +
                    "<option name='truest_or_falsest' value='f'>Falsest</option>" +
                    "</select>"
                );

                $("#options").append(
                    " <input name='truest_or_falsest_count' size='3'>"
                );

                $("#operator_options").append("</form>");
                break;
        }

    });

    $("#new_operator_select option:contains(" + node_current_operator + ")").attr('selected', 'selected');

}

eems_operator_changes={};

function updateEEMSOperator(node_id, alias, new_operator, options){
    eems_operator_changes[node_id]=[];
    eems_operator_changes[node_id].push(new_operator);
    eems_operator_changes[node_id].push(options);

    $("#" + node_id + "_current_operator").html(new_operator);
    $("#" + node_id + "_current_operator").addClass("eems_changed_node_style");
}

function updateEEMSThresholds(node_id,alias, true_threshold, false_threshold){
    $("#" + node_id + "_current_operator").addClass("eems_changed_node_style");
    eems_operator_changes[node_id]=[];
    eems_operator_changes[node_id].push("Covert to Fuzzy", [true_threshold,false_threshold]);
}

function modify_eems(){
    alertify.alert(
        "<div id='eems_available_action_form'></div>"
        , function (e, str) {
            if (e) {
                var true_threshold = $("#true_threshold").val();
                var false_threshold = $("#false_threshold").val();
                updateEEMSThresholds(node_id, alias, true_threshold,false_threshold);
            }
        }
    ).set('labels', {OK:'Cancel'});

    eems_available_actions = results["eems_available_actions"];
    var count = 0
    $("#eems_available_action_form").append("<ol id='eems_available_action_form_list'>");
    $.each(eems_available_actions, function(action){
        $("#eems_available_action_form_list").append("<li>" + action + "</li><br>")
    });
}

