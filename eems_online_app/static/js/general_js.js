$( document ).ready(function() {

    $("#files").prop('value', '');

    // Add the list of available eems_online_models to the dropdown menu
    $.each(eems_online_models_json, function(key,value){

        var available_eems_online_model_name =  value.toString().split(',')[0];
        $("#eems_model_dropdown").append("<option value='" + key + "'>" + available_eems_online_model_name + "</option>");
    });

    // Set the eems model dropdown menu to the first option on page load.
    $('#eems_model_dropdown option').eq(1).prop('selected', true).trigger('change');


    // Initialize MEEMSE with the JSON file below
    init_eems_file = "static/eems/json_models/HighSiteSensitivityFz.json"
    init_eems_file_name = init_eems_file.split("/").pop();
    init_eems_model = init_eems_file_name.split(".")[0];
    eems_model_id = 1;
    $.get(init_eems_file, function(results) {
        json = JSON.parse(results);
        init(json,init_eems_file_name);
    });

    eems_online_model_name = init_eems_model;
    eems_model_modified_id = '';

    // Initialize EEMS bundled command changes dictionary
    eems_bundled_commands = {};
    eems_bundled_commands["action"] = "ProcessCmds";
    eems_bundled_commands["cmds"] = [];
    eems_bundled_commands["cmds"].push({"action": "LoadProg", "progNm": eems_online_model_name});
    eems_children_dict = {}

});

// Change model (drop-down)
$('#eems_model_dropdown').change(function(){

        eems_model_modified_id = '';

        // Get the JSON file and render the model
        if ($('#eems_model_dropdown option:selected').text() != "") {

            $("#user_defined_model").html("")

            var eems_online_json_file_name = eems_online_models_json[this.value][0][1];
            var path_to_json_file = "static/eems/json_models/" + eems_online_json_file_name;

            eems_online_model_name = eems_online_models_json[this.value][0][0];

            eems_model_id = this.value

            $.get(path_to_json_file, function (results) {
                var json_model = JSON.parse(results);
                init(json_model, eems_online_model_name);
            });
        }

        reset_eems_bundled_commands()

    }
);

// File upload button
$('input:file').change(function(e){
        var filename=e.target.files[0].name
        $("#user_defined_model").html(filename.replace('.json','').replace('.JSON',''))
        $('#eems_model_dropdown option').eq(0).prop('selected', true).trigger('change');
        var startByte = e.target.getAttribute('data-startbyte');
        var endByte = e.target.getAttribute('data-endbyte');

        reset_eems_bundled_commands()

        // function defined in the file_upload.js script.
        readBlob(startByte, endByte, filename);
        // Calls function below
    }
);

// Loads a user's EEMS command file into the database.
function load_eems_user_model(eems_filename, eems_file_contents) {

    alert(eems_file_contents);

    $.ajax({
        url: "/load_eems_user_model", // the endpoint
        type: "POST", // http method
        data: {
            'eems_filename': eems_filename,
            'eems_file_contents': eems_file_contents
        },

        // handle a successful response
        success: function (json) {
            //results = JSON.parse(json)
            eems_user_model_id = JSON.parse(json["eems_model_id"])
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                " <a href='#' class='close'>&times;</a></div>");
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

// Run EEMS Button
$("#run_eems_button").click(function(){run_eems(eems_model_id)});

// Send the user defined changes to the back end and run EEMS.
function run_eems() {

    eems_bundled_commands["cmds"].push({"action": "RunProg"})

    eems_operator_changes_string = JSON.stringify(eems_bundled_commands)

    $.ajax({
        url: "/run_eems", // the endpoint
        type: "POST", // http method
        data: {
            'eems_model_id': eems_model_id,
            'eems_model_modified_id': eems_model_modified_id,
            'eems_operator_changes_string': eems_operator_changes_string
        },

        // handle a successful response
        success: function (response) {
            eems_model_modified_id = response
            alertify.alert("<div id='model_run_complete_alert'><img id='check_icon' src='static/img/check.png'><span id='model_run_complete_alert_text'>Model Run Complete</span></div>")
            console.log("EEMS Model ID: " + eems_model_modified_id)
            console.log("EEMS Command Modifications: ")
            console.log(JSON.stringify(eems_bundled_commands))
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                " <a href='#' class='close'>&times;</a></div>");
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });

}

// On settings icon click, create a dialog box that allows the user to change the EEMS operator.
function changeEEMSOperator(node_id, alias, node_current_operator, children_string) {

    var children_array = children_string.split(',');

    if (node_current_operator == "Convert To Fuzzy"){
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
        );

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

    update_cmd_dict = {};

    update_cmd_dict["action"] = 'UpdateCmd';
    update_cmd_dict["cmd"] = {};
    update_cmd_dict["cmd"]["rsltNm"] = node_id;
    update_cmd_dict["cmd"]["cmd"] = new_operator;
    update_cmd_dict["cmd"]["params"] = {};

    update_cmd_dict["cmd"]["params"]["InFieldNames"] = [];

    $.each(eems_children_dict[node_id], function(count, value) {
        // ToDO: Not sure why the children in the JSON files have a ":number" after the file name.
        var child_name=value.split(":")[0];
        update_cmd_dict["cmd"]["params"]["InFieldNames"].push(child_name);
    });

    eems_bundled_commands["cmds"].push(update_cmd_dict);

    $("#" + node_id + "_current_operator").html(new_operator);
    $("#" + node_id + "_current_operator").addClass("eems_changed_node_style");
}

function updateEEMSThresholds(node_id,alias, true_threshold, false_threshold){
    $("#" + node_id + "_current_operator").addClass("eems_changed_node_style");
    eems_operator_changes[node_id]=[];
    eems_operator_changes[node_id].push("Covert to Fuzzy", [true_threshold,false_threshold]);
}

function reset_eems_bundled_commands(){
    eems_bundled_commands = {};
    eems_bundled_commands["action"] = "ProcessCmds";
    eems_bundled_commands["cmds"] = [];
    eems_bundled_commands["cmds"].push({"action": "LoadPog", "progNm": eems_online_model_name});
}
