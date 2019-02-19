var map = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }
).setView([37,-126.5], 6);

// Basemaps
topographic=L.esri.basemapLayer("Topographic").addTo(map);
gray=L.esri.basemapLayer("Gray")
national_geographic=L.esri.basemapLayer("NationalGeographic")
imagery=L.esri.basemapLayer("Imagery")
oceans=L.esri.basemapLayer("Oceans")
shaded_relief=L.esri.basemapLayer("ShadedRelief")
usa_topo=L.esri.basemapLayer("USATopo")

var groupedOverlays = {
    "Base Maps": {
        'Gray': gray,
        'Topographic': topographic,
        'National Geographic': national_geographic,
        'Oceans': oceans,
        'Imagery': imagery,
        'Shaded Relief': shaded_relief,
        'USA Topo': usa_topo,
    },
    "Reference Layers": {
    }
};

L.control.zoom({
     position:'topright'
}).addTo(map);

//DYNAMIC LEGEND
var dynamic_legend = L.control({position: 'bottomright'});

//Initialize Legend
dynamic_legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend');
    div.innerHTML = "";
    return div;
};

dynamic_legend.addTo(map)

var options = { exclusiveGroups: ["Reporting Units","Base Maps"], position:'topright'};
L.control.groupedLayers("", groupedOverlays, options).addTo(map);

function swapImageOverlay(layer_name, eems_model_id, delay_speed) {

    last_layer_clicked=layer_name

    if (typeof image_overlay != "undefined") {
        old_image_overlay = image_overlay
        $(old_image_overlay._image).fadeOut(delay_speed, function () {
            map.removeLayer(old_image_overlay);
        });
    }

    var image_overlay_url = "static/eems/models/" + eems_model_id + "/overlay/" + layer_name + ".png?" + new Date().getTime();
    image_overlay = L.imageOverlay(image_overlay_url, overlay_bounds).addTo(map);
    $(image_overlay._image).fadeIn(delay_speed);

    //image_overlay.bringToBack();

    swapLegend(layer_name, eems_model_id)
}

function swapLegend(layer_name, eems_model_id){
    document.getElementsByClassName('info')[0].innerHTML = "<div id='LegendHeader'>" + layer_name + "</div>" +
        "<img class='legend_png'  src='static/eems/models/" + eems_model_id + "/overlay/" + layer_name + "_key.png?" + new Date().getTime() +"'>" +
        "<div class='legendLabels'>"
}

//Opacity/transparency slider on image overlays
var handle = document.getElementById('handle'),
    start = false,
    startTop;

document.onmousemove = function(e) {
    if (!start) return;
    // Adjust control.
    handle.style.top = Math.max(-5, Math.min(78, startTop + parseInt(e.clientY, 10) - start)) + 'px';

    fillOpacityLevel=(1 - (handle.offsetTop / 80));

    // Adjust opacity on image overlays.
    image_overlay.setOpacity(fillOpacityLevel);
    $(".legend_png").css("opacity", fillOpacityLevel)

};

handle.onmousedown = function(e) {
    // Record initial positions.
    start = parseInt(e.clientY, 10);
    startTop = handle.offsetTop - 5;
    return false;
};

document.onmouseup = function(e) {
    start = null;
};

elements=document.getElementsByClassName('ui-opacity')
//Transparency slider

for (var i = 0; i < elements.length; i++) {
    elements[i].style.display = elements[i].style.display = 'inline';
}

var marker = null;
var json_eems_results = null;

function on_map_click(e) {

    last_map_click = e;

    $(".eems_value").remove();
    $(".node").append("<div class='eems_value'><img class='eems_value_spinner' src='static/img/eems_value_spinner.gif'></div>");

    if (marker !== null) {
        map.removeLayer(marker);
    }
    wkt = "POINT(" + e.latlng.lng + " " + e.latlng.lat + ")";
    marker = new L.marker(e.latlng).addTo(map);

    $.ajax({
        url: "/get_raster_data", // the endpoint
        type: "POST", // http method
        data: {
            'wkt': wkt,
            'model_id': eems_model_id_for_map_display,
            'original_model_id': eems_model_id,
        },

        // handle a successful response
        success: function (results) {

            json_eems_results = JSON.parse(results);
            update_tree_values(json_eems_results)
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
        }
    });
}

map.on('click', on_map_click);

function update_tree_values(json_eems_results) {
    $.each(json_eems_results, function (key, value) {
        $(".eems_value").remove().promise().then(function () {
            $("#" + key).append("<div class='eems_value'>" + value + "</div>");
        });
    });
}

$("#map_original_button").on("click", function(){
    swapImageOverlay(last_layer_clicked,eems_model_id,1000);
    eems_model_id_for_map_display = eems_model_id;
    if (typeof last_map_click != "undefined") {
        on_map_click(last_map_click);
    }
});

$("#map_modified_button").on("click", function(){
    swapImageOverlay(last_layer_clicked,eems_model_modified_id,1000);
    eems_model_id_for_map_display = eems_model_modified_id;
    if (typeof last_map_click != "undefined") {
        on_map_click(last_map_click);
    }
});

