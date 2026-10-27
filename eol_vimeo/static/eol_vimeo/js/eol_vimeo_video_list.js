require(
    [
        "domReady!",
        "jquery",
        "js/views/video/transcripts/editor"
    ],
    function(doc, $, Editor) {
        var config = JSON.parse(
            document.getElementById("basic-vimeo-config").textContent
        );

        var html_id = config.htmlId;
        var tabName = config.tabName;
        var course_id = config.courseId;
        var edx_selected_video_id = config.edx_selected_video_id;
        var eol_video_list = config.eol_video_list;

        // edx_video_id de los videos subidos por eol_vimeo (relación antigua con edxval)
        var eol_edx_video_ids = eol_video_list.map(function (video) { return video.edx_video_id; });

        var transcripts = new Editor({
            el: $('#editor-tab-'+html_id).find('.basic_metadata_edit')
        });

        var storage = TabsEditingDescriptor.getStorage();

        TabsEditingDescriptor.Model.addModelUpdate(
            html_id,
            tabName,
            function () {
                // Advanced, Save
                metadataEditor = storage.MetadataEditor;

                if (metadataEditor) {
                    transcripts.syncAdvancedTab(metadataEditor.collection, metadataEditor);
                }
            }
        );

        TabsEditingDescriptor.Model.addOnSwitch(
            html_id,
            tabName,
            function () {
                // Basic
                metadataEditor = storage.MetadataEditor;

                if (metadataEditor) {
                    transcripts.syncBasicTab(metadataEditor.collection, metadataEditor);
                }
            }
        );

        const editor_container = transcripts.$el;
        const video_url_view = transcripts.settingsView.views.video_url;
        const video_id_view = transcripts.settingsView.views.edx_video_id;
        const video_id_container = video_id_view.$el;
        video_id_container.hide();

        // Guarda un valor en el modelo de un campo del editor y avisa del cambio
        function setFieldValue(view, value) {
            view.model.attributes.value = value;
            view.model.attributes.explicitly_set = true;
            view.model.changed.value = value;
            transcripts.handleFieldChanged();
        }

        // Video seleccionado actualmente:
        // 1. por url en html5_sources (relación nueva)
        // 2. por edx_video_id (bloques aún no migrados)
        function getSelectedVideo() {
            const current_sources = video_url_view.model.get('value') || [];
            let selected = eol_video_list.find(function (video) {
                return video.url_vimeo && current_sources.indexOf(video.url_vimeo) !== -1;
            });
            if (!selected && edx_selected_video_id) {
                selected = eol_video_list.find(function (video) {
                    return video.edx_video_id === edx_selected_video_id;
                });
            }
            return selected;
        }

        // https://player.vimeo.com/external/<id>... o https://player.vimeo.com/progressive_redirect/playback/<id>/...
        const VIMEO_ID_PATTERN = /player\.vimeo\.com\/(?:external|progressive_redirect\/playback)\/(\d+)/;
        function extractVimeoIdFromUrl(url) {
            if (!url || typeof url !== 'string') {
                return '';
            }
            const match = url.trim().match(VIMEO_ID_PATTERN);
            return match ? match[1] : '';
        }

        function getCookie(name) {
            const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
            return match ? decodeURIComponent(match[1]) : '';
        }

        // Promise con la url del thumbnail ('' si no hay o falla).
        // force=true hace POST: se salta la BD, consulta Vimeo y guarda el resultado en EolVimeoVideo.
        function getVimeoThumb(vimeo_id, force) {
            if (!vimeo_id) {
                return Promise.resolve('');
            }
            const options = {
                method: force ? 'POST' : 'GET',
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            };
            if (force) {
                // fetch no agrega el token CSRF como lo hace $.ajax en Studio
                options.headers['X-CSRFToken'] = getCookie('csrftoken');
            }
            return fetch('/eolvimeo/thumbnail/' + encodeURIComponent(vimeo_id), options).then(function (response) {
                return response.ok ? response.json() : {};
            }).then(function (data) {
                return data.thumbnail_url || '';
            }).catch(function () {
                return '';
            });
        }

        function getVideoByEdxId(edx_video_id) {
            return eol_video_list.find(function (video) {
                return video.edx_video_id === edx_video_id;
            });
        }

        // create html thumbnail start as hide
        thumbnail_editor_html = `
        <li class="field comp-setting-entry metadata_entry" id="eol-update-thumbnail-${html_id}-container" style="display: none;">
            <div class="wrapper-comp-setting">
                <label class="label setting-label">`+gettext("Update thumbnail from Vimeo")+`</label>
                <button id="eol-update-${html_id}" class="action setting-upload update-vimeo" type="button" data-tooltip="`+gettext("Update")+`" data-videoid="" value="`+gettext("Update")+`">`+gettext("Update")+`</button>
            </div>
            <span class="tip setting-help">
                <div id="ui-loading-update" class="ui-loading is-hidden">
                    <p>
                        <span class="spin"><span class="icon fa fa-refresh" aria-hidden="true"></span></span>
                        <span class="copy">`+gettext("Updating")+`</span>
                    </p>
                </div>
            </span>
            <span id="eol-update-response" class="tip setting-help"></span>
        </li>
        `   
        // add thumbnail picture
        editor_container.find('ul.list-input.settings-list').append(thumbnail_editor_html);
        // thumbnail_editor_container is the container of the update thumbnail button
        const thumbnail_editor_container = editor_container.find('#eol-update-thumbnail-' + html_id + '-container');
        // video_url_input is the input field of the video url
        const video_url_input = $('#'+video_url_view.uniqueId);
        // create video select
        editor_container.find('ul.list-input.settings-list').prepend(`
            <li class="field comp-setting-entry metadata_entry">
                <div class="wrapper-comp-setting">
                <label class="label setting-label">`+gettext("Select a video")+`</label>
                    <select id="eol-video-${html_id}">
                        <option value="">`+gettext("External video link")+`</option>
                    </select>
                    <span class="tip setting-help">
                        `+gettext("Select a video previously uploaded to the course or insert an external link in the corresponding field.")+`
                    </span>
                </div>
            </li>
        `);
        
        // Create video options (the value is only used inside the selector, it is not saved in the block)
        const selected_video = getSelectedVideo();
        eol_video_list.forEach(video => {
            const isSelected = selected_video !== undefined && video.edx_video_id === selected_video.edx_video_id;
            $(`#eol-video-${html_id}`).append(
                $('<option>', {
                    value: video.edx_video_id,
                    selected: isSelected
                }).text(video.display_name)
            );
        });
        if (selected_video) {
            thumbnail_editor_container.show();
            thumbnail_editor_container.find(`#eol-update-${html_id}`).attr('data-vimeoid', extractVimeoIdFromUrl(selected_video.url_vimeo));
            video_url_input.val(selected_video.url_vimeo);
            video_url_input.prop('readonly', true);
        }

        // Detect change in video selector
        $('#eol-video-' + html_id).on('change', function(e) {
            const video = getVideoByEdxId(e.target.value);
            const video_url = video ? video.url_vimeo : '';

            // Show or hide the update thumbnail button and lock the video url input when a video is selected
            if (video) {
                video_url_input.prop('readonly', true);
                thumbnail_editor_container.show();
            }
            else{
                video_url_input.prop('readonly', false);
                thumbnail_editor_container.hide();
            }
            // Update the data-vimeoid attribute of the update thumbnail button with the selected Vimeo ID
            thumbnail_editor_container.find(`#eol-update-${html_id}`).attr('data-vimeoid', extractVimeoIdFromUrl(video_url));

            // Save the vimeo url in html5_sources (video_url field)
            video_url_input.val(video_url);
            video_url_input.trigger('change');
            setFieldValue(video_url_view, video_url ? [video_url] : []);

            // Cut the old relation with edxval: if the block points to an eol_vimeo edx_video_id, clear it.
            // Any other edx_video_id is kept (e.g. the "external video" Studio creates to store transcripts).
            const current_video_id = (video_id_container.find('input').val() || '').trim();
            if (current_video_id && eol_edx_video_ids.indexOf(current_video_id) !== -1) {
                video_id_container.find('input').val('');
                video_id_container.find('input').trigger('change');
                setFieldValue(video_id_view, '');
            }
        });

        // Add update thumbnail function: forces the refresh from Vimeo and saves it in EolVimeoVideo
        $('#eol-update-' + html_id).bind('click', function(e) {
            const button = e.currentTarget;
            $('#ui-loading-update').show();
            button.disabled = true;
            getVimeoThumb(button.dataset.vimeoid, true).then(function (thumb_url) {
                if (thumb_url) {
                    $('#eol-update-response').text(gettext("Update thumbnail from Vimeo"));
                }
                else {
                    $('#eol-update-response').text(gettext("There was an error updating the thumbnail."));
                }
                $('#ui-loading-update').hide();
                button.disabled = false;
            });
        });
    }
);