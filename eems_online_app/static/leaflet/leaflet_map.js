var map = L.map('map', {
        zoomControl: false
    }
).setView([39,-96], 5);

L.control.zoom({
     position:'topleft'
}).addTo(map);

var OpenStreetMap=L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', { attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a>' }).addTo(map);


