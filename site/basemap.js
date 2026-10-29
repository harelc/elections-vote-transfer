/**
 * Raster basemap for MapLibre pages.
 *
 * CARTO free key from https://carto.com/basemaps/apikey/
 * (domain-locked; visible in the client by design).
 *
 * positron → light_all, dark_matter → dark_all (old CartoDB style names).
 */
(function (global) {
    'use strict';

    const CARTO_API_KEY = 'cb1_33zt_1_905a903d849a3633cd99904d';
    const CARTO_ATTR =
        '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>';

    const STYLE_PATH = {
        positron: 'light_all',
        dark_matter: 'dark_all',
        voyager: 'voyager',
    };

    if (!document.getElementById('maplibre-chrome')) {
        const style = document.createElement('style');
        style.id = 'maplibre-chrome';
        style.textContent = [
            '.maplibregl-map{font-family:Heebo,sans-serif;}',
            '.maplibregl-popup-content{background:#1e212a;color:#f3f5f8;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.4);padding:12px 14px;}',
            '.maplibregl-popup-anchor-bottom .maplibregl-popup-tip{border-top-color:#1e212a;}',
            '.maplibregl-popup-anchor-top .maplibregl-popup-tip{border-bottom-color:#1e212a;}',
            '.maplibregl-popup-close-button{color:#939aab;font-size:18px;}',
            '.maplibregl-ctrl-group{background:#232733;border:1px solid #3a4050;}',
            '.maplibregl-ctrl-group button{filter:invert(1);}',
            '.maplibregl-ctrl-attrib{background:rgba(22,24,29,.85);color:#939aab;}',
            '.maplibregl-ctrl-attrib a{color:#f0b429;}',
        ].join('');
        document.head.appendChild(style);
    }

    function tileUrls(style) {
        const path = STYLE_PATH[style] || style || 'light_all';
        const key = encodeURIComponent(CARTO_API_KEY);
        return ['a', 'b', 'c', 'd'].map(function (sub) {
            return 'https://' + sub + '.basemaps.cartocdn.com/rastertiles/' + path + '/{z}/{x}/{y}.png?key=' + key;
        });
    }

    function rasterStyle(styleName, darken) {
        const style = styleName || 'positron';
        const paint = { 'raster-opacity': 1 };
        if (darken && style === 'positron') {
            paint['raster-brightness-max'] = 0.72;
            paint['raster-saturation'] = -0.15;
        }
        return {
            version: 8,
            sources: {
                basemap: {
                    type: 'raster',
                    tiles: tileUrls(style),
                    tileSize: 256,
                    attribution: CARTO_ATTR,
                    maxzoom: 20,
                },
            },
            layers: [
                { id: 'basemap-bg', type: 'background', paint: { 'background-color': '#16181d' } },
                { id: 'basemap', type: 'raster', source: 'basemap', paint: paint },
            ],
        };
    }

    function createMap(container, opts) {
        opts = opts || {};
        const map = new maplibregl.Map({
            container: container,
            style: rasterStyle(opts.basemap || 'positron', opts.darken !== false),
            center: opts.center || [34.9, 31.5],
            zoom: opts.zoom == null ? 8 : opts.zoom,
            minZoom: opts.minZoom == null ? 7 : opts.minZoom,
            maxZoom: opts.maxZoom == null ? 18 : opts.maxZoom,
            maxBounds: opts.maxBounds || null,
            attributionControl: true,
            preserveDrawingBuffer: !!opts.preserveDrawingBuffer,
        });
        if (opts.zoomControl !== false) {
            map.addControl(
                new maplibregl.NavigationControl({ showCompass: false }),
                opts.zoomPosition || 'top-left'
            );
        }
        map.latLngToContainerPoint = function (ll) {
            return map.project([ll.lng, ll.lat]);
        };
        map.setView = function (center, zoom) {
            const lat = Array.isArray(center) ? center[0] : center.lat;
            const lng = Array.isArray(center) ? center[1] : center.lng;
            map.easeTo({ center: [lng, lat], zoom: zoom });
        };
        map.fitBounds = function (latlngs, fitOpts) {
            const pts = latlngs.map(function (p) {
                return [p[1], p[0]];
            });
            let west = Infinity, south = Infinity, east = -Infinity, north = -Infinity;
            pts.forEach(function (p) {
                west = Math.min(west, p[0]);
                east = Math.max(east, p[0]);
                south = Math.min(south, p[1]);
                north = Math.max(north, p[1]);
            });
            let padding = (fitOpts && fitOpts.padding) || 40;
            if (Array.isArray(padding)) padding = padding[0];
            map.fitBounds([[west, south], [east, north]], {
                padding: padding,
                maxZoom: fitOpts && fitOpts.maxZoom,
            });
        };
        return map;
    }

    function whenMapReady(map, fn) {
        if (map.isStyleLoaded()) fn();
        else map.once('load', fn);
    }

    function upsertGeoJSON(map, id, data) {
        const src = map.getSource(id);
        if (src) src.setData(data);
        else map.addSource(id, { type: 'geojson', data: data });
    }

    global.createMap = createMap;
    global.whenMapReady = whenMapReady;
    global.upsertGeoJSON = upsertGeoJSON;
})(window);
