// TODO: Break this out to actually work more dynamically/other places
// and also get data as needed directly from DB
// This will rely heavily on whatever geographic information system is leveraged
// Get lat, lon, zoom level from URL if exists
// --------- Helper Functions --------- //

function generateHSLtable(num) {
    var table = [];
    for (i = 0; i < 360; i += 360 / num) {
        var c = {};
        c.hue = Math.random() * 360;
        c.saturation = 30 + Math.random() * 20;
        c.lightness = 30 + Math.random() * 20;
        table.push(c);
    }
    return table;
};

$.getJSON('/api/leaflet_map/' + window.iced.app_name).then(function (mapPayload) {
    mapPayload = JSON.parse(mapPayload)

    // Get lat, lon, zoom level from URL if exists
    var url = window.location.href.split('/');
    if ((url[4]=='sitemap') && (url.length==9)) {
        // check regex
        if ((/-?(\d+)\.?\d*/.test(url[6])) && (/-?(\d+)\.?\d*/.test(url[7])) && (/(\d+)/)) {
            var inLat = url[6];
            var inLon = url[7];
            var inZoom = url[8];
        }
    };


    // Initiate map
    var map = L.map('map', {
        fullscreenControl: true,
        defaultExtentControl: true,
        attributionControl: false,
        zoom: 0
    }).setView([46.252389, 6.941528],16);

    // GB changed the above so that the home button will take you to the Pierre des Marmettes, the largest erratic in Switzerland, originally recognized as a glacial erratic by Jean de Charpentier in 1840. Previously the home button went to a random location in Washington. Perhaps it should be a global view instead?


    // get tiles
    var satellite = L.gridLayer.googleMutant({
            type: 'satellite' // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
    });

    var terrain = L.gridLayer.googleMutant({
            type: 'terrain' // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
    }).addTo(map);

    var hybrid = L.gridLayer.googleMutant({
            type: 'hybrid' // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
    });

    ///*

    // ICED geohash regions
    var maxSamples = mapPayload.regions.features.map(
        function(r){
            return parseInt(r.properties.nsamples)
        })
        .sort(
            function(a,b){
                return a-b
        })
        .slice(-1)[0]


    var ICED_regions = L.geoJSON(mapPayload.regions, {
    pointToLayer: function (feature, latlng) {
        var minRadius = 4;
        var maxRadius = 8;
            var circleOptions = {
                    color: "#e65100",
                    fillColor: "#ffb74d",
                    weight: 2,
                    radius: feature.properties.nsamples/maxSamples * (maxRadius-minRadius) + minRadius,
                    fillOpacity: 0.85,
                    pane: "markerPane"
            };

            var tooltipOptions = {
                    permanent:false,
                    className: "myCSSClass"
            };

            return L.circleMarker(latlng, circleOptions).bindTooltip(feature.properties.nsamples + " Samples", tooltipOptions).openTooltip();
    }
    });


    // Get all ICED sites
    var sample_name = [];
    var site_longname = [];
    var site_shortname = [];
    var site_id = [];
    var region = [];
    var what = [];
    var lat = [];
    var lon = [];
    for (var i=0; i<mapPayload.samples.features.length; i++) {
            sample_name[i] = mapPayload.samples.features[i].properties.sample_name;
            site_longname[i] = mapPayload.samples.features[i].properties.site_longname;
            site_shortname[i] = mapPayload.samples.features[i].properties.site;
            site_id[i] = mapPayload.samples.features[i].properties.site_id;
            region[i] = mapPayload.samples.features[i].properties.region;
            what[i] = mapPayload.samples.features[i].properties.what;
            lat[i] = mapPayload.samples.features[i].geometry.coordinates[1];
            lon[i] = mapPayload.samples.features[i].geometry.coordinates[0];
    };

    //--------Get random Region for initial map view-------------

    var region_unique = [...new Set(region)];

    // random integer
    var random = Math.floor(Math.random() * (+region_unique.length));

    // get indicies of samples in this region
    var indicies = [];
    var theseSamples = [];
    latsInRandomRegion = [];
    lonsInRandomRegion = [];
    var idx = region.indexOf(region_unique[random]);
    while (idx != -1) {
        indicies.push(idx);
        latsInRandomRegion.push(lat[idx]);
        lonsInRandomRegion.push(lon[idx]);
        idx = region.indexOf(region_unique[random], idx + 1);
    }

    // Average lat and lon
    let average = (array) => array.reduce((a, b) => a + b) / array.length;
    latMean = average(latsInRandomRegion);
    lonMean = average(lonsInRandomRegion);

    // Set initial map view. Default is to use a random site unless URL parameters are passed (e.g. ?x=-122&y=47&z=7)
    if ((typeof inLat !== 'undefined') && (typeof inLon !== 'undefined') && (typeof inZoom !== 'undefined')) {
        map.setView([inLat,inLon], inZoom);
        if (document.getElementById('randomRegion') !== null) {
            document.getElementById('randomRegion').innerHTML = "";
        };
    } else {
            map.setView([latMean, lonMean], 7);
            if (document.getElementById('randomRegion') !== null) {
              document.getElementById('randomRegion').innerHTML = "Randomly selected area: " + region_unique[random];
            };
    };

    //--------Done setting initial map view-------------

    // Get unique sites
    var site_shortname_unique = [...new Set(site_shortname)];


    function makeSiteGroup(customStyles) {
        return new L.MarkerClusterGroup({
            maxClusterRadius: 15,
            spiderfyOnMaxZoom: true,
            removeOutsideVisibleBounds: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: false,
            singleMarkerMode: true,
            animateAddingMarkers: false,
            disableClusteringAtZoom: 20,
            spiderfyDistanceMultiplier: 0.9,
            spiderLegPolylineOptions: { weight: 1, color: '#5e5e5e'},
            clusterPane: "markerPane",
            iconCreateFunction: function(cluster) {
                var count = cluster.getChildCount();
                var digits = (count + '').length;
                return new L.DivIcon({
                    iconSize: null,
                    html: '<div class="cn-cluster-inner" style="' + customStyles + '">' + count + '</div>',
                    className: 'cn-cluster digits digits-' + digits
                });
            }
        });
    }

    var colorTable = generateHSLtable(site_shortname_unique.length); // Generate unique color value
    var siteGroups = {};

    // FeatureMarker: extends the L.Marker class options parameter to store a properties object (database attributes, mainly)
    FeatureMarker = L.Marker.extend({
        options: {
            properties: {}
        }
    });

    // Leaflet Layer Group
    var samplesLayerGroup = L.layerGroup();

    // random integer for setting initial map view
    //var random = Math.floor(Math.random() * (+site_shortname_unique.length));

    // loop through unique sites
    for (var i=0; i<site_shortname_unique.length; i++) {
            var this_site_shortname = site_shortname_unique[i];
            var hsl = colorTable[i];
            var css = 'background:hsl(' + hsl.hue + ',' + hsl.saturation + '%,' + hsl.lightness + '%);'
            css += 'background:hsla(' + hsl.hue + ',' + hsl.saturation + '%,' + hsl.lightness + '%, 0.9);'
            siteGroups[this_site_shortname] = makeSiteGroup(css);

            // find indicies of samples at this site
            var indicies = [];
            var idx = site_shortname.indexOf(this_site_shortname);
            while (idx != -1) {
                    indicies.push(idx);
                    idx = site_shortname.indexOf(this_site_shortname, idx + 1);
            }

            var subsetMarkers = [];

            // loop through samples and make a marker for each
            for (var j=0; j<indicies.length; j++) {
                    var m = new FeatureMarker(L.latLng(parseFloat(lat[indicies[j]]), parseFloat(lon[indicies[j]])), {
                            title: site_longname[indicies[j]], // name displayed on hover
                            riseOnHover: true
                    });
                    m.bindTooltip(sample_name[indicies[j]],  {permanent:false, className: "myCSSClass"});
                    var html = '<table class="cn-popup-content"><tr><th  colspan="2", align=center>' +
                            sample_name[indicies[j]]  +
                            "<tr><td colspan=2><hr></td></tr></th></tr>" +
                            '<tr><td><b>Latitude:</b></td><td>' + lat[indicies[j]] + '</td></tr>' +
                            '<tr><td><b>Longitude:</b></td><td>' + lon[indicies[j]] + '</td></tr>' +
                            '<tr><td><b>Region:</b></td><td>' + region[indicies[j]] + '</td></tr>' +
                                                    '<tr><td><b>Region</b></td><td>' + region[indicies[j]] + '</td></tr>' +
                            '<tr><td><b>Site:</b></td><td>' + site_longname[indicies[j]] + '</td></tr>' +
                                                    '<tr><td><b>What is it?</b></td><td>' + what[indicies[j]] + '</td></tr>' +
                                                    '<tr><td colspan=2><hr></td></tr>' +
                                                    '<tr><td colspan=2><a href=\"' + window.location.origin + '/' + window.iced.app_name + '/site/' + site_shortname[indicies[j]] + '\" target=\"_blank\">Site page</a>' +
                                                    '<tr><td colspan=2><a href=\"' + window.location.origin + '/' + window.iced.app_name + '/sample/' + sample_name[indicies[j]] + '\" target=\"_blank\">Sample page</a>';
                    m.bindPopup(html);
                    subsetMarkers.push(m);
            };

            siteGroups[this_site_shortname].addLayers(subsetMarkers);
            siteGroups[this_site_shortname].on('clusterclick', function(e) {
                    e.layer.spiderfy();
            });
            siteGroups[this_site_shortname].addTo(samplesLayerGroup);
    };
    samplesLayerGroup.addTo(map);


    // Control marker visibility
    map.on('zoomend', function() {
        if (map.getZoom() < 7){
            if (map.hasLayer(samplesLayerGroup)) {
                map.removeLayer(samplesLayerGroup);
            };
            if (map.hasLayer(ICED_regions)) {
            } else {
                map.addLayer(ICED_regions);
            };
        }

        if (map.getZoom() >= 7){
            if (map.hasLayer(ICED_regions)) {
                map.removeLayer(ICED_regions);
            };
            if (map.hasLayer(samplesLayerGroup)){
            } else {
                map.addLayer(samplesLayerGroup);
            };
        }
    });

    // Control settings
    var basemaps = {"Terrain": terrain, "Satellite": satellite, "Satellite + labels + roads": hybrid};
    var overlays = {};
    L.control.layers(basemaps, overlays, {collapsed:false}).addTo(map);
    L.control.scale({metric:true, imperial:false, position: "bottomright"}).addTo(map);
    L.control.mousePosition({position:"bottomright"}).addTo(map);
});