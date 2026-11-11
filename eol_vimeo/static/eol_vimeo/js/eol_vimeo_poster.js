(function () {
    'use strict';

    // Se carga en LMS (courseware.html), Studio (container.html) y en el editor de video (eol_vimeo_video_list.html).
    if (window.EolVimeoUtils) {
        return;
    }

    function extractVimeoIdFromUrl(url) {
        if (!url || typeof url !== 'string') {
            return '';
        }
        const match = url.trim().match(/player\.vimeo\.com\/(?:external|progressive_redirect\/playback)\/(\d+)/);
        return match ? match[1] : '';
    }

    function getVimeoThumb(vimeo_id) {
        if (!vimeo_id) {
            return Promise.resolve('');
        }
        const options = {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        };
        return fetch('/eolvimeo/thumbnail/' + encodeURIComponent(vimeo_id), options)
            .then(function (response) { return response.ok ? response.json() : {}; })
            .then(function (data) { return data.thumbnail_url || ''; })
            .catch(function () { return ''; });
    }

    // Compartidas con eol_vimeo_video_list.js (editor de video en Studio)
    window.EolVimeoUtils = {
        extractVimeoIdFromUrl: extractVimeoIdFromUrl
    };

    function getSrc(video) {
        var candidatos = [];
        var source = video.querySelector('source');
        if (source) {
            candidatos.push(source.getAttribute('src'));
        }
        candidatos.push(video.getAttribute('src'));
        var meta = video.closest('.video[data-metadata]');
        if (meta) {
            try {
                var sources = JSON.parse(meta.getAttribute('data-metadata')).sources;
                if (Array.isArray(sources)) {
                    candidatos = candidatos.concat(sources);
                }
            }
            catch (e) {
                console.log('[vimeo-thumbs] data-metadata inválido', e);
            }
        }
        for (var i = 0; i < candidatos.length; i++) {
            if (extractVimeoIdFromUrl(candidatos[i])) {
                return candidatos[i];
            }
        }
        return '';
    }

    function ponerPoster(video) {
        var vimeo_id = extractVimeoIdFromUrl(getSrc(video));
        if (!vimeo_id) {
            return;
        }
        getVimeoThumb(vimeo_id).then(function (thumb_url) {
            console.log('[vimeo-thumbs] vimeo_id', vimeo_id, ', thumb:', thumb_url);
            if (thumb_url) {video.setAttribute('poster', thumb_url);}
        });
    }

    console.log('[vimeo-thumbs] start', location.href);
    // los videos que ya estan cargados
    document.querySelectorAll('.video-player video').forEach(ponerPoster);
    // los que carguen despues (cambio de unidad, pestañas de la secuencia, etc)
    document.addEventListener('loadstart', function (e) { if (e.target.matches('.video-player video')) { ponerPoster(e.target); } }, true);
})();