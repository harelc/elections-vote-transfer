/**
 * Clustered ballot dots on a MapLibre map.
 * Unclustered stations are WebGL circles. Clusters are HTML markers so the
 * existing pie-chart icons can stay.
 */
(function (global) {
    'use strict';

    function clusterLeaves(source, id, count) {
        const result = source.getClusterLeaves(id, count, 0);
        if (result && typeof result.then === 'function') return result;
        return new Promise(function (resolve, reject) {
            source.getClusterLeaves(id, count, 0, function (err, features) {
                if (err) reject(err);
                else resolve(features);
            });
        });
    }

    function StationClusterLayer(map, handlers) {
        this.map = map;
        this.handlers = handlers || {};
        this.items = [];
        this.clusterMarkers = [];
        this.token = 0;
        this.ready = false;
        this.popup = null;
    }

    StationClusterLayer.prototype.setStations = function (items) {
        this.items = items;
        const data = {
            type: 'FeatureCollection',
            features: items.map(function (item, i) {
                return {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [item.lng, item.lat] },
                    properties: { i: i, color: item.color, radius: item.radius },
                };
            }),
        };
        const self = this;
        const apply = function () {
            if (!self.map.getSource('stations')) {
                self.map.addSource('stations', {
                    type: 'geojson',
                    data: data,
                    cluster: true,
                    clusterRadius: 50,
                    clusterMaxZoom: 16,
                });
                self.map.addLayer({
                    id: 'station-circles',
                    type: 'circle',
                    source: 'stations',
                    filter: ['!', ['has', 'point_count']],
                    paint: {
                        'circle-radius': ['get', 'radius'],
                        'circle-color': ['get', 'color'],
                        'circle-opacity': 0.75,
                        'circle-stroke-width': 1,
                        'circle-stroke-color': '#111318',
                    },
                });
                self.map.addLayer({
                    id: 'station-clusters',
                    type: 'circle',
                    source: 'stations',
                    filter: ['has', 'point_count'],
                    paint: { 'circle-radius': 1, 'circle-opacity': 0 },
                });
                self.bindEvents();
            } else {
                self.map.getSource('stations').setData(data);
            }
            self.ready = true;
            self.syncClusters();
        };
        if (this.map.isStyleLoaded()) apply();
        else this.map.once('load', apply);
    };

    StationClusterLayer.prototype.bindEvents = function () {
        const self = this;
        const map = this.map;
        map.on('mousemove', 'station-circles', function (e) {
            const feature = e.features && e.features[0];
            if (!feature) return;
            const item = self.items[Number(feature.properties.i)];
            if (!item || !self.handlers.onStationEnter) return;
            map.getCanvas().style.cursor = 'pointer';
            self.handlers.onStationEnter(item, e.point);
        });
        map.on('mouseleave', 'station-circles', function () {
            map.getCanvas().style.cursor = '';
            if (self.handlers.onStationLeave) self.handlers.onStationLeave();
        });
        map.on('click', 'station-circles', function (e) {
            const feature = e.features && e.features[0];
            if (!feature) return;
            const item = self.items[Number(feature.properties.i)];
            if (item && self.handlers.onStationClick) self.handlers.onStationClick(item);
        });
        map.on('moveend', function () { self.syncClusters(); });
        map.on('idle', function () { self.syncClusters(); });
    };

    StationClusterLayer.prototype.clearClusterMarkers = function () {
        this.clusterMarkers.forEach(function (marker) { marker.remove(); });
        this.clusterMarkers = [];
    };

    StationClusterLayer.prototype.syncClusters = async function () {
        if (!this.ready || !this.map.getSource('stations')) return;
        const token = ++this.token;
        const features = this.map.querySourceFeatures('stations', {
            filter: ['has', 'point_count'],
        });
        const seen = new Set();
        const clusters = [];
        features.forEach(function (feature) {
            const id = feature.properties.cluster_id;
            if (seen.has(id)) return;
            seen.add(id);
            clusters.push(feature);
        });
        const source = this.map.getSource('stations');
        const built = [];
        for (let c = 0; c < clusters.length; c++) {
            const feature = clusters[c];
            const count = feature.properties.point_count;
            let leaves = [];
            try {
                leaves = await clusterLeaves(source, feature.properties.cluster_id, count);
            } catch (err) {
                continue;
            }
            if (token !== this.token) return;
            const stations = leaves.map(function (leaf) {
                return this.items[Number(leaf.properties.i)];
            }, this).filter(Boolean);
            const lng = feature.geometry.coordinates[0];
            const lat = feature.geometry.coordinates[1];
            const icon = this.handlers.clusterHTML
                ? this.handlers.clusterHTML(stations, lng, lat)
                : { html: String(count), className: 'custom-cluster', size: 40 };
            const el = document.createElement('div');
            el.className = icon.className || 'custom-cluster';
            el.style.width = icon.size + 'px';
            el.style.height = icon.size + 'px';
            el.innerHTML = icon.html;
            const self = this;
            el.addEventListener('mouseenter', function () {
                if (self.handlers.onClusterEnter) self.handlers.onClusterEnter(stations, lng, lat);
            });
            el.addEventListener('mouseleave', function () {
                if (self.handlers.onClusterLeave) self.handlers.onClusterLeave();
            });
            el.addEventListener('click', function (event) {
                event.stopPropagation();
                if (self.handlers.onClusterClick) {
                    self.handlers.onClusterClick(stations, lng, lat, feature.properties.cluster_id);
                } else {
                    self.zoomCluster(feature.properties.cluster_id, lng, lat);
                }
            });
            built.push(new maplibregl.Marker({ element: el, anchor: 'center' }).setLngLat([lng, lat]));
        }
        if (token !== this.token) return;
        this.clearClusterMarkers();
        const self = this;
        built.forEach(function (marker) {
            marker.addTo(self.map);
            self.clusterMarkers.push(marker);
        });
    };

    StationClusterLayer.prototype.zoomCluster = function (id, lng, lat) {
        const source = this.map.getSource('stations');
        const map = this.map;
        const result = source.getClusterExpansionZoom(id);
        const go = function (zoom) {
            map.easeTo({ center: [lng, lat], zoom: zoom });
        };
        if (result && typeof result.then === 'function') result.then(go);
        else source.getClusterExpansionZoom(id, function (err, zoom) { if (!err) go(zoom); });
    };

    StationClusterLayer.prototype.showPopup = function (lng, lat, html) {
        if (this.popup) this.popup.remove();
        this.popup = new maplibregl.Popup({ maxWidth: '320px', className: 'station-popup-container' })
            .setLngLat([lng, lat])
            .setHTML(html)
            .addTo(this.map);
    };

    global.StationClusterLayer = StationClusterLayer;

    global.asLeafletCluster = function (stations, lng, lat) {
        const markers = stations.map(function (item) {
            return {
                options: { stationData: item.station },
                getLatLng: function () { return { lat: item.origLat, lng: item.origLng }; },
            };
        });
        return {
            getAllChildMarkers: function () { return markers; },
            getLatLng: function () { return { lat: lat, lng: lng }; },
        };
    };
})(window);
