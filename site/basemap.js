/**
 * Raster basemap for Leaflet pages.
 *
 * CARTO free key from https://carto.com/basemaps/apikey/
 * (domain-locked; visible in the client by design).
 *
 * positron → light_all, dark_matter → dark_all (old CartoDB style names).
 * Pass 'voyager' for CARTO's sample style.
 */
(function (global) {
    'use strict';

    const CARTO_API_KEY = 'cb1_33zt_1_905a903d849a3633cd99904d';

    const CARTO_ATTR =
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

    const STYLE_PATH = {
        positron: 'light_all',
        dark_matter: 'dark_all',
        voyager: 'voyager',
    };

    function addBasemap(map, style) {
        style = style || 'positron';
        const path = STYLE_PATH[style] || style;
        if (CARTO_API_KEY) {
            L.tileLayer(
                'https://{s}.basemaps.cartocdn.com/rastertiles/' + path + '/{z}/{x}/{y}.png?key=' + encodeURIComponent(CARTO_API_KEY),
                { attribution: CARTO_ATTR, subdomains: 'abcd', maxZoom: 20 }
            ).addTo(map);
            return;
        }

        const dark = style === 'dark_matter';
        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/' +
                (dark ? 'World_Dark_Gray_Base' : 'World_Light_Gray_Base') +
                '/MapServer/tile/{z}/{y}/{x}',
            { attribution: 'Tiles &copy; <a href="https://www.esri.com/">Esri</a>', maxZoom: 16 }
        ).addTo(map);
        if (!dark) {
            L.tileLayer(
                'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
                { maxZoom: 16 }
            ).addTo(map);
        }
    }

    global.addBasemap = addBasemap;
})(window);
