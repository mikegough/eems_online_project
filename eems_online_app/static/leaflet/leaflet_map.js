var map = L.map('map', {
        zoomControl: false
    }
).setView([39,-96], 5);

// Basemaps
gray=L.esri.basemapLayer("Gray").addTo(map);
topographic=L.esri.basemapLayer("Topographic")
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
     position:'topleft'
}).addTo(map);

//DYNAMIC LEGEND
var dynamic_legend = L.control({position: 'bottomleft'});

//Initialize Legend
dynamic_legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend');
    div.innerHTML=""
    return div;
};

dynamic_legend.addTo(map)

var options = { exclusiveGroups: ["Reporting Units","Base Maps"], position:'topleft'};
L.control.groupedLayers("", groupedOverlays, options).addTo(map);

function swapImageOverlay(layerName) {

    if (typeof image_overlay != "undefined") {
        map.removeLayer(image_overlay);
    }

    var image_overlay_url = "static/eems/models/" + eems_model_id + "/overlay/png/" + layerName + ".png";
    image_overlay = L.imageOverlay(image_overlay_url, overlay_bounds);
    image_overlay.addTo(map);
    image_overlay.bringToBack();

    swapLegend(layerName)
}

function swapLegend(layerName){
    document.getElementsByClassName('info')[0].innerHTML = "<div id='LegendHeader'>" + layerName + "</div>" +
              "<img style='float:left' src='static/eems/models/" + eems_model_id + "/overlay/legend/" + layerName + "_legend.png'>" +
              "<div class='legendLabels'>"
}
