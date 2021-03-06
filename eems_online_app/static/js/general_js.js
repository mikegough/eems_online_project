$( document ).ready(function() {

    <!-- Resize Meemse Container -->

    var max_height = $("#control_panel_and_meemse_container").height();
    var max_width = $(window).width();
    var max_width = 640;

    $( "#control_panel_and_meemse_container" ).resizable({
        minHeight:183,
        minWidth:0,
        //maxWidth:max_width,
        maxHeight:max_height,

        start: function(){
        },
        resize: function(){
            if ($(this).width() < 470) {
                $("#save_eems_div").addClass("stay_put");
            }
            else {
                $("#save_eems_div").removeClass("stay_put");
            }
        },

        stop: function(){
            st.canvas.resize($("#meemse_container").width(),$("#meemse_container").height());
        }
    });


    $("#files").prop('value', '');

    // Add the list of available eems_online_models to the dropdown menu
    $.each(eems_online_models_json, function(index, object){

        $.each(object, function(id,array){
            var available_eems_online_model_name =  array[0];
            var available_eems_online_model_extent =  array[1];
            $("#eems_model_dropdown").append("<option extent='" + available_eems_online_model_extent + "' value='" + index + "'>" + available_eems_online_model_name + "</option>");
        })
    });

    // Set the initial model parameters
    // Set the eems model dropdown menu to the initial eems model on page load

    eems_model_id = initial_eems_model_json[0][0];

    eems_model_id_for_map_display = eems_model_id;

    $("#eems_model_dropdown option[value=" + eems_model_id + "]").attr('selected', 'selected').trigger("change");

    init_eems_file_name = initial_eems_model_json[0][1][1];
    init_eems_file =  "static/eems/models/" + eems_model_id_for_map_display + "/tree/meemse_tree.json";
    init_eems_model = init_eems_file_name.split(".")[0];

    $.getJSON(init_eems_file, function(results) {
        json = results;
        init(json,init_eems_file_name);
    });

    eems_online_model_name = init_eems_model;
    eems_model_modified_id = '';

    // Initialize EEMS bundled command changes dictionary
    eems_bundled_commands = {};
    eems_bundled_commands["action"] = "ProcessCmds";
    eems_bundled_commands["cmds"] = [];
    eems_children_dict = {}

});

// Change model (drop-down)
$('#eems_model_dropdown').change(function(){

        $("#button_div").hide();
        $("#run_eems_button").addClass("disabled");
        $("#download_label").addClass("disabled");
        $("#link_label").addClass("disabled");

        overlay_bounds = JSON.parse($(this).find('option:selected').attr('extent'));

        eems_model_modified_id = '';
        eems_model_current_model = $("#eems_model_dropdown option:selected").text();

        // Get the JSON file and render the model
        if ($('#eems_model_dropdown option:selected').text() != "") {

            $("#run_eems_button").addClass("disabled");
            $("#quality_selector_div").addClass("disabled");
            $('#map_quality').attr('disabled', 'disabled');

            $("#user_defined_model").html("");

            eems_model_id = this.value;
            eems_model_id_for_map_display = this.value;

            var path_to_json_file = "static/eems/models/" + eems_model_id_for_map_display + "/tree/meemse_tree.json";

            eems_online_model_name = eems_online_models_json[this.value][0][0];
            eems_online_model_description = eems_online_models_json[this.value][0][2];
            $("#model_info_contents").html("<span id='model_info_header'>Model Description:</span> " + eems_online_model_description + "<span id='model_info_more'> Learn more...</span>");

            $("#model_info_more").on("click", function(){
                get_additional_info(eems_model_id)
            });

            $.getJSON(path_to_json_file, function (results) {
                var json_model = results;
                init(json_model, eems_online_model_name);
            });
        }

        current_arguments_dict={};

        reset_eems_bundled_commands()
    }
);

// File upload button
$('input:file').change(function(e){

        var filename=e.target.files[0].name;
        $("#user_defined_model").html(filename.replace('.json','').replace('.JSON',''));
        $('#eems_model_dropdown option').eq(0).prop('selected', true).trigger('change');
        var startByte = e.target.getAttribute('data-startbyte');
        var endByte = e.target.getAttribute('data-endbyte');

        reset_eems_bundled_commands();

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
$("#run_eems_button").click(function(){run_eems(0)});

// Send the user defined changes to the back end and run EEMS.
function run_eems(download) {

    $("#run_eems_button").addClass("disabled");
    $("#quality_selector_div").addClass("disabled");
    $('#map_quality').attr('disabled', 'disabled');
    var map_quality = $("#map_quality").val();

    eems_operator_changes_string = JSON.stringify(eems_bundled_commands);
    $("#spinner_div").show()
    if (! download ){
        $("#spinner_text").html("Running EEMS...")
    }
    else {
        $("#spinner_text").html("Preparing data for download....")
    }

    return $.ajax({
        url: "/run_eems", // the endpoint
        type: "POST", // http method
        data: {
            'eems_model_id': eems_model_id,
            'eems_model_modified_id': eems_model_modified_id,
            'eems_operator_changes_string': eems_operator_changes_string,
            'download': download,
            'map_quality': map_quality
        },
        success: function (json_response) {
            var response = JSON.parse(json_response);
            eems_model_modified_id = response.eems_model_modified_id;
            if (response.error_code == '1'){
                var error_message = response.error_message;
                alertify.alert("<div id='error_alert'><div id='alert_icon_div'><img id='alert_icon' src='static/img/alert.png'></div>There was an error processing your request. Please refer to the error log below for information on how to correct the error.<div id='error_alert_text'>Error: " + error_message + "</div></div>")
            }
            else {
                if (! download) {
                    alertify.alert("<div id='model_run_complete_alert'><img id='check_icon' src='static/img/check.png'><span id='model_run_complete_alert_text'>Model Run Complete</span></div>")
                }
                console.log("EEMS Model ID: " + eems_model_modified_id);
                console.log("EEMS Command Modifications: ");
                console.log(JSON.stringify(eems_bundled_commands, null, 2));
                $("#download_label").removeClass("disabled");
                $("#link_label").removeClass("disabled");
                $("#button_div").show();
                eems_model_id_for_map_display = eems_model_modified_id;
                swapImageOverlay(last_layer_clicked, eems_model_id_for_map_display);
                $("#run_eems_div").addClass("disabled");
            }
        },
        error: function (xhr, errmsg, err) {
            var error_message = xhr.responseText;
            //var eems_error =  error_message.split("\n")[1]
            alertify.alert("<div class='error_message_context'>There was an error processing your request. If the problem persists, please reload the page.<div class='error_message'>Error: " + error_message + "</div></div>")
        },
        complete: function(){
            $("#spinner_div").hide()
        }
    });
}


$('#download_label').click(function(e) {

    $("#download_label").addClass("disabled");
    $("#link_label").addClass("disabled");

    $.when(run_eems(1)).done(function(){

        $("#download_file").attr("src", "static/img/spinner.gif");

        $.ajax({
            url: "/download", // the endpoint
            type: "POST", // http method
            data: {
                'eems_model_modified_id': eems_model_modified_id,
            },
            success: function (response) {
                e.preventDefault();  //stop the browser from following
                // window.open with "_parent" instead of window.location to fix spinner freezing.
                window.open("static/eems/models/zip/EEMS_Online_Model_Results_" + eems_model_modified_id + ".zip", "_parent")
            },
            error: function (xhr, errmsg, err) {
                alertify.alert("There was an error in processing your request. Please try again. If the problem persists, please reload the page.")
            },
            complete: function () {
                $("#download_file").attr("src", "static/img/download.png");
                $("#download_label").removeClass("disabled");
                $("#quality_selector_div").removeClass("disabled");
                $('#map_quality').removeAttr('disabled');
                $("#link_label").removeClass("disabled");
            }

        });
    });
});

$('#link_label').click(function(e) {

    alertify.alert("<div id='link_text'> Right click and copy the link below to share these results or access them at a later time: <p><textarea readonly='readonly' id='link' href='" + hostname_for_link + "?model=" + eems_model_modified_id + "'>" + hostname_for_link + "?model=" + eems_model_modified_id + "</textarea></div>")
    var textBox = document.getElementById("link");
    textBox.onfocus = function() {
        textBox.select();

        // Work around Chrome's little problem
        textBox.onmouseup = function() {
            // Prevent further mouseup intervention
            textBox.onmouseup = null;
            return false;
        };
    };

    if (typeof link_already_generated == 'undefined') {
        $.ajax({
            url: "/link", // the endpoint
            type: "POST", // http method
            data: {
                'eems_model_id': eems_model_id,
                'eems_model_modified_id': eems_model_modified_id,
            },
            success: function (response) {
            },
            error: function (xhr, errmsg, err) {
                alertify.alert("There was an error in processing your request. Please try again. If the problem persists, please reload the page.")
            },
            complete: function () {
            }

        });
    }

    link_already_generated = true

});

function showHistogram(node_id, alias) {
        form_string =  "<div class='histogram_div' ><img class='histogram_img_read' src='static/eems/models/" + eems_model_id_for_map_display + "/histogram/" + node_id + ".png'></div>";
        alertify.alert(form_string)
}

var eems_operator_changes={};
var eems_operator_exclusions=["Read", "Copy", "EEMSRead", "EEMSWrite", "FuzzyNot"];
var changed_params_list=[];

// Triggered after users clicks the settings icon created in spacetree.js
function changeEEMSOperator(node_id, alias, node_original_operator, children_string, original_arguments) {

    // Get the current operator out of the div at the bottom of the node (used to set the selected dropdown option).
    var current_operator = $("#" + node_id + "_current_operator").html();

    var children_array = children_string.split(',');

    // Create the form...
    form_string =  "<table id='form_table'><tr><td>";
    form_string +=  "<div id='form_div'><b>Operator: </b>";
    form_string += "<select id='new_operator_select'>";

        //Add the compatible EEMS operators to the dropdown.
        // Convert to Fuzzy Options
        if (node_original_operator.toLowerCase().indexOf("convert to fuzzy") != -1) {
            $.each(eems_available_commands_json, function (index, operator) {
                if (operator["DisplayName"].toLowerCase().indexOf("convert to fuzzy") != -1) {
                    form_string += "<option cmdName='" + operator['Name'] + "' value='" + index + "'>" + operator["DisplayName"] + "</option>"
                }
            });
            var histogram_toggle = true
        }

        // Fuzzy Options
        else {
            if (node_original_operator.indexOf("Fuzzy") != -1) {
                $.each(eems_available_commands_json, function (index, operator) {
                    if ($.inArray(operator["Name"], eems_operator_exclusions) == -1 && operator["DisplayName"].toLowerCase().indexOf("convert to fuzzy") == -1 && operator["DisplayName"].indexOf("Fuzzy") != -1) {
                        form_string += "<option cmdName='" + operator['Name'] + "' value='" + index + "'>" + operator["DisplayName"] + "</option>"
                    }
                });
            }

            // Non-Fuzzy Options
            else {
                $.each(eems_available_commands_json, function (index, operator) {
                    if ($.inArray(operator["DisplayName"], eems_operator_exclusions) == -1 && operator["DisplayName"].toLowerCase().indexOf("Fuzzy") == -1) {
                        form_string += "<option cmdName='" + operator['Name']  + "' value='" + operator["Name"] + "'>" + operator["DisplayName"] + "</option>"
                    }
                });
            }

            var histogram_toggle = false
        }

    form_string += "</select>";
    form_string += "<span id='eems_operator_info'><img src='static/img/info.png'></span>";
    if (current_operator.replace(/\s+/g, '') != node_original_operator.replace(/\s+/g, '')) {
        form_string += "<div class='original_operator'><b>Original Operator: </b>" + node_original_operator + "</div>"
    }
    //Create an empty div for operator params
    form_string += "<form id='eems_operator_params'></form>";
    form_string += "</td><td>";
    if (histogram_toggle){
        form_string += "<div id='histogram_to_show_div'>"
        form_string += "<input checked name='histogram_to_show' type='radio' value='" + node_id + "'>This Node";
        form_string += "<input name='histogram_to_show' type='radio' value='" + children_array[0] + "'>Input Node";
        form_string += "</div>";
    }
    form_string +=  "<div class='histogram_div'><img id='histogram_img' src='static/eems/models/" + eems_model_id_for_map_display + "/histogram/" + node_id + ".png'></div>";
    form_string += "</div>";
    form_string += "</td></tr></table>"

    // Create and open the tool dialog box. On confirm store the new operator data in a dictionary.
    alertify.confirm(form_string, function (e, str) {
        if (e) {
            var new_operator = $("#new_operator_select option:selected").attr("cmdName");
            var new_operator_name = $("#new_operator_select option:selected").text();
            var $inputs = $('#eems_operator_params :input');

            var new_operator_id = $("#new_operator_select option:selected").val();

            // Get the user entered required parameters.
            required_params = {};
            $inputs.each(function (index) {
                required_params[$(this).attr('id')] = $(this).val();
            });

            // Store the user-defined operators & last set of arguments in a dictionary, so that they can be recalled later.
            current_arguments_dict[node_id][new_operator] = {}
            $('#eems_operator_params *').filter(':input').each(function () {
                current_arguments_dict[node_id][new_operator][this.id] = this.value;
            });

            // If the user updated the node operator already, delete the old one.
            $.each(eems_bundled_commands["cmds"], function (index, cmd_object) {
                if (typeof cmd_object["action"] != "undefined" && cmd_object["action"] == "UpdateCmd") {
                    if (cmd_object["cmd"]["rsltNm"] == node_id) {
                        eems_bundled_commands["cmds"].splice(index, 1);
                    }
                }
            });

            // Call function to store new eems operator and options in a dictionary
            updateEEMSOperator(node_id, alias, new_operator, required_params, new_operator_name, new_operator_id);
            $("#run_eems_button").removeClass("disabled");
            $("#quality_selector_div").removeClass("disabled");
            $("#map_quality").removeAttr("disabled");
            $("#run_eems_div").removeClass("disabled");
            $("#download_label").addClass("disabled");
            $("#link_label").addClass("disabled");

        }
    });

    // ON Convert to Fuzzy operators, allow the user to toggle the histogram between the current node and the input node.
    $('input[type=radio][name=histogram_to_show]').change(function() {
        node_id_to_show_on_histogram = $('input[name=histogram_to_show]:checked').val()
        $("#histogram_img").attr("src", "static/eems/models/" + eems_model_id_for_map_display + "/histogram/" + node_id_to_show_on_histogram + ".png")
    })


    // Pick appropriate operators to show & bind change event
    bind_params(node_id, children_array, node_original_operator, original_arguments);

    // Set the selected dropdown item to the current operator, and trigger a change.
    $("select option").filter(function () {
        if (current_operator.replace(/ /g, "") == node_original_operator.replace(/ /g, "")) {
            return $(this).text().toLowerCase() == node_original_operator.toLowerCase();
        } else {
            // If the user has changed the operator, show the current operator
            return $(this).text().toLowerCase() == current_operator.toLowerCase();
        }
    }).prop('selected', true).change();
}

current_arguments_dict={};

function bind_params(node_id, children_array, node_original_operator, original_arguments) {

    // Operator specific options. Happens on dropdown change. Triggered when the user first clicks the gear AND on subsequent operator changes.
    $("#new_operator_select").on("change", function () {

        $("#eems_operator_params").empty();

        // Get the new operator from the dropdown.
        var new_operator = $("#new_operator_select option:selected").attr("cmdName");
        var new_operator_name = $("#new_operator_select option:selected").text();

        if (typeof current_arguments_dict[node_id] == "undefined") {
           current_arguments_dict[node_id] = {}
        }

        // Split the argument string on the arbitrary deliniater specified in spacetree.js
        // Move outside the loop below, so that the original arguments can be written out to the form.
        current_arguments_parsed = original_arguments.split('**##**');

        // If the user hasn't clicked on this settings icon before, set the default arguments to the original arguments
        if (! (new_operator in current_arguments_dict[node_id]) ) {

            current_arguments_dict[node_id][new_operator]={};

            // If the new operator is the same as the original operator, get the arguments from the original Spacetree node arguments.
            if (new_operator_name.toLowerCase() == node_original_operator.toLowerCase()) {

                // Make a dictionary out of the arguments
                $.each(current_arguments_parsed, function (index, kv_pair) {
                    current_arguments_dict[node_id][new_operator][kv_pair.split(":")[0]] = kv_pair.split(":")[1]

                });
            }
        }

        $("#eems_operator_info").prop('title', eems_available_commands_json[this.value]["ShortDesc"]);

        $("#eems_operator_params").html("<p><b>Input Nodes:</b><br>");
        $.each(children_array, function(index,child) {
            $("#eems_operator_params").append(child.split(":")[0] + "<br>");
        });

        // Have to handle "Convert to Fuzzy" differently since the arguments we need are OPTIONAL parameters.
        if (eems_available_commands_json[this.value]["Name"] == 'CvtToFuzzy'){

            if (typeof current_arguments_dict[node_id][new_operator]['TrueThreshold'] == "undefined") {
                    current_arguments_dict[node_id][new_operator]["TrueThreshold"] = "";
                    current_arguments_dict[node_id][new_operator]["FalseThreshold"] = "";
            }

            $("#eems_operator_params").append("<p><b>Optional Parameters:</b><br>");
            $("#eems_operator_params").append("TrueThreshold: <input id='TrueThreshold' type='text' value='" + current_arguments_dict[node_id][new_operator]['TrueThreshold'] +"'><img title='Float' src='static/img/info.png'><br>");
            $("#eems_operator_params").append("FalseThreshold <input id='FalseThreshold' type='text' value='" + current_arguments_dict[node_id][new_operator]['FalseThreshold'] +"'><img title='Float' src='static/img/info.png'><br>");

            $("#form_table").append("<tr><td colspan='2'><div class='original_params'><b>Original input values: </b>" + current_arguments_parsed + "</td></tr></div>")
        }


        // Get the list of required params for the selected operator ....
        var required_params = eems_available_commands_json[this.value]["ReqParams"];
        delete required_params["InFieldNames"];
        delete required_params["InFieldName"];

        //  Write out the required params input fields. If there was something entered previously or this is the original operator, write out the current arguments...
        if (! $.isEmptyObject(required_params)) {
            $("#eems_operator_params").append("<p><b>Required Parameters:</b><br>");
            $.each(required_params, function (key, value) {
                if (typeof current_arguments_dict[node_id][new_operator][key] == "undefined") {
                    current_arguments_dict[node_id][new_operator][key] = ""
                }
                    $("#eems_operator_params").append(key + ": " + "<input id='" + key + "'type='text' value='" + current_arguments_dict[node_id][new_operator][key] + "'>" + "<img title='" + value + "' src='static/img/info.png'><br>");
            });
            $("#eems_operator_params").append("<div class='original_params'><b>Original input values: </b>" + current_arguments_parsed + "</div>")
        }

    });

}

function updateEEMSOperator(node_id, alias, new_operator, required_params, new_operator_name, new_operator_id){

    // Update. Pass in new_operator_name for setting the display name.

    var update_cmd_dict = {};

    update_cmd_dict["action"] = 'UpdateCmd';
    update_cmd_dict["cmd"] = {};
    update_cmd_dict["cmd"]["rsltNm"] = node_id;
    update_cmd_dict["cmd"]["cmd"] = new_operator;
    update_cmd_dict["cmd"]["params"] = {};

    // MPilot needs the list of InFieldNames as a string within brackets. A list won't work.
    if (new_operator.toLowerCase().indexOf("cvttofuzzy") == -1) {
        update_cmd_dict["cmd"]["params"]["InFieldNames"] = '[';
        $.each(eems_children_dict[node_id], function(count, value) {
            // ToDO: Not sure why the children in the JSON files have a ":number" after the file name.
            var child_name=value.split(":")[0];
            update_cmd_dict["cmd"]["params"]["InFieldNames"] += child_name + ",";
        });
        // Remove the trailing comma.
        update_cmd_dict["cmd"]["params"]["InFieldNames"] = update_cmd_dict["cmd"]["params"]["InFieldNames"].slice(0,-1);
        update_cmd_dict["cmd"]["params"]["InFieldNames"] += ']';
    }
    // For Convert To Fuzzy operators, the key is "InFieldName" (singular), and it is not a list.
    else {
        $.each(eems_children_dict[node_id], function(count, value) {
            var child_name=value.split(":")[0];
            update_cmd_dict["cmd"]["params"]["InFieldName"] = child_name;
        });

    }

    $.each(required_params, function(param, value) {
        // ToDO: Not sure why the children in the JSON files have a ":number" after the file name.
        value = value.replace(/ /g,"");
        var child_name=value.split(":")[0];
        // Check the required parameter type stored in eems_available_commands_json. If it's a list, add the brackets.
        if (typeof eems_available_commands_json[new_operator_id]["ReqParams"][param] != "undefined" && (eems_available_commands_json[new_operator_id]["ReqParams"][param][0]).indexOf("List") != -1) {
            update_cmd_dict["cmd"]["params"][param] = "[" + value + "]";
        }
        else {
            update_cmd_dict["cmd"]["params"][param] = value;
        }
    });

    eems_bundled_commands["cmds"].push(update_cmd_dict);

    $("#" + node_id + "_current_operator").html(new_operator_name);
    $("#" + node_id + "_current_operator").addClass("eems_changed_node_style");
}

function reset_eems_bundled_commands(){

    eems_bundled_commands = {};
    eems_bundled_commands["action"] = "ProcessCmds";
    eems_bundled_commands["cmds"] = [];
}

$('#map_original_button').on('click', function () {
    swapImageOverlay(last_layer_clicked,eems_model_id);
    eems_model_id_for_map_display = eems_model_id;
    $("#map_original_button").addClass('selected');
    $("#map_modified_button").removeClass('selected');
});

$('#map_modified_button').on('click', function () {
    swapImageOverlay(last_layer_clicked,eems_model_modified_id);
    eems_model_id_for_map_display = eems_model_modified_id;
    $("#map_modified_button").addClass('selected');
    $("#map_original_button").removeClass('selected');
});

$("#save_icon").on('click', function() {
        html2canvas(document.getElementById("meemse_container"), {
            onrendered: function (canvas) {
                var img = canvas.toDataURL();
                var link = document.createElement('a');
                link.href = img;
                link.download = "eems_model_diagram_" + eems_model_current_model + "_" + eems_model_id + ".jpg";
                document.body.appendChild(link);
                link.click();
            }
        });
});

$("#expand_icon").on('click', function(){
    st.onClick(st.root);
    $("#meemse_container").addClass("fixed_meemse");
    $("#canvas_controls").addClass("fixed_canvas_controls");
    $("#infovis-canvaswidget").width("100%");
    st.canvas.resize(screen.width,$("#meemse_container").height());
    st.controller.constrained=false;
    $("#expand_div").hide();
    $("#collapse_div").show();
    $("#meemse_container").resizable('disable');
});

$("#collapse_icon").on('click', function(){
    $("#meemse_container").removeClass("fixed_meemse");
    $("#canvas_controls").removeClass("fixed_canvas_controls");
    $("#infovis-canvaswidget").width("52.5%");
    st.controller.constrained=true;
    $("#expand_div").show();
    $("#collapse_div").hide();
    st.canvas.resize(840,751);
    $("#meemse_container").resizable('enable');
});

function get_additional_info(eems_model_id){

    $.ajax({
        url: "/get_additional_info", // the endpoint
        type: "POST", // http method
        data: {
            'eems_model_id': eems_model_id,
        },

        // handle a successful response
        success: function (response) {
            var json_additional_info = JSON.parse(response)
            model_name = json_additional_info["name"];
            long_description = json_additional_info["long_description"];
            author = json_additional_info["author"];
            creation_date = json_additional_info["creation_date"];
            alertify.alert("<div class='long_description'><div class='long_description_header'>Model: </div>" + model_name + "<br><div class='long_description_header'>Author: </div>" + author +"<br><div class='long_description_header'>" + "Creation Date: </div>" + creation_date + "</p><div class='long_description_header'>Description</div></p>" + long_description + "</div>");
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
        }
    });
}

$("#about_link").on('click', function(){
    $("#about").show();
    $("#home").hide();
    $("#contact").hide();
    $("#about_link").addClass('active');
    $("#home_link").removeClass('active');
    $("#contact_link").removeClass('active')
});

$("#home_link").on('click', function(){
    $("#about").hide();
    $("#home").show();
    $("#contact").hide();
    $("#about_link").removeClass('active');
    $("#home_link").addClass('active');
    $("#contact_link").removeClass('active')
});

$("#contact_link").on('click', function(){
    $("#about").hide();
    $("#home").hide();
    $("#contact").show();
    $("#about_link").removeClass('active');
    $("#home_link").removeClass('active');
    $("#contact_link").addClass('active');
});

