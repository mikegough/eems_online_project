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

function changeEEMSOperator(node_id, alias, node_current_operator) {
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
                    updateEEMSThresholds(node_id, alias, true_threshold,false_threshold)
                }
            }
        )

    }
    else if (["Difference", "Weighted Sum"].includes(node_current_operator)){
        alertify.confirm(
            "<div id='change_operator_form'><b>Node: </b>" + alias +
            "<p><b>Operator: </b><select id='new_operator_select'>" +
            "<option name='new_operator' value='Difference'>Difference</option>" +
            "<option name='new_operator' value='Weighted Sum'>Weighted Sum</option>" +
            "</select>" +
            "</div>"
            , function (e, str) {
                if (e) {
                    var new_operator = $("#new_operator_select option:selected").text();
                    updateEEMSOperator(node_id, alias, new_operator)
                }
            }
        );
    }
    else {
        alertify.confirm(
            "<div id='change_operator_form'><b>Node: </b>" + alias +
            "<p><b>Operator: </b><select id='new_operator_select'>" +
            "<option name='new_operator' value='And'>And</option>" +
            "<option name='new_operator' value='Or'>Or</option>" +
            "<option name='new_operator' value='Negative Or'>Negative Or</option>" +
            "<option name='new_operator' value='Union'>Union</option>" +
            "<option name='new_operator' value='Selected Union'>Selected Union</option>" +
            "<option name='new_operator' value='Weighted Union'>Weighted Union</option>" +
            "</select>" +
            "</div>"
            , function (e, str) {
                if (e) {
                    var new_operator = $("#new_operator_select option:selected").text();
                    updateEEMSOperator(node_id, alias, new_operator)
                }
            }
        );
    }

    $("#new_operator_select option:contains(" + node_current_operator + ")").attr('selected', 'selected');
}

eems_operator_changes={}
function updateEEMSOperator(node_id,alias, new_operator){
    //alertify.success(alias  + " operator will be changed to " + new_operator);
    $("#" + node_id + "_current_operator").html(new_operator)
    $("#" + node_id + "_current_operator").addClass("eems_changed_node_style")
    eems_operator_changes[node_id]=[]
    eems_operator_changes[node_id].push(new_operator)
}

function updateEEMSThresholds(node_id,alias, true_threshold, false_threshold){
    //alertify.success(alias  + " operator will be changed to " + new_operator);
    $("#" + node_id + "_current_operator").addClass("eems_changed_node_style")
    eems_operator_changes[node_id]=[]
    eems_operator_changes[node_id].push("Covert to Fuzzy", [true_threshold,false_threshold])
}


