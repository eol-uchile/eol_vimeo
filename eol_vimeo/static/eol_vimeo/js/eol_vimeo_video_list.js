require(
    [
        "domReady!",
        "jquery",
        "js/views/video/transcripts/editor"
    ],
    function(doc, $, Editor) {
        function getVideoUrlById(list, id) {
            let url = undefined;
            list.forEach(element => {
                if (element.edx_video_id === id)
                    {url = element.url_vimeo}
            });
            return url;
        };
        var config = JSON.parse(
            document.getElementById("basic-vimeo-config").textContent
        );

        var html_id = config.htmlId;
        var tabName = config.tabName;
        var course_id = config.courseId;
        var edx_selected_video_id = config.edx_selected_video_id;
        var eol_video_list = config.eol_video_list;

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

        let currentUrl = undefined;        
        const editor_container = transcripts.$el
        const video_id_container = transcripts.settingsView.views.edx_video_id.$el
        video_id_container.hide();


        // create html thumbnail start as hide
        thumbnail_editor_html = `
        <li class="field comp-setting-entry metadata_entry" id="eol-update-thumbnail-${html_id}-container" style="display: none;">
            <div class="wrapper-comp-setting">
                <label class="label setting-label">`+gettext("Update thumbnail from Vimeo")+`</label>
                <button id="eol-update-${html_id}" class="action setting-upload update-vimeo" type="button" data-tooltip="`+gettext("Update")+`" data-videoid="${edx_selected_video_id}" value="`+gettext("Update")+`">`+gettext("Update")+`</button>
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
        const video_url_input = $('#'+transcripts.settingsView.views.video_url.uniqueId);
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
        
        // Create video options
        eol_video_list.forEach(video => {
            const isSelected = video.edx_video_id === edx_selected_video_id;
            if (isSelected) {
                thumbnail_editor_container.show();
                currentUrl = video.url_vimeo;
                video_url_input.val(currentUrl);
                video_url_input.prop('readonly', true);
            }
            $(`#eol-video-${html_id}`).append(
                $('<option>', {
                    value: video.edx_video_id,
                    selected: isSelected
                }).text(video.display_name)
            );
        });

        // Detect change in video selector
        $('#eol-video-' + html_id).on('change', function(e) {
            video_url_input.val('');

            // Show or hide the update thumbnail button based on if is selected a video ID and hide or show the video url input field
            if (e.target.value != ""){
                video_url_input.prop('readonly', true);
                currentUrl = getVideoUrlById(eol_video_list, e.target.value);
                video_url_input.val(currentUrl);
                thumbnail_editor_container.show();
            }
            else{
                video_url_input.prop('readonly', false);
                thumbnail_editor_container.hide();
            }
            // Update the data-videoid attribute of the update thumbnail button with the selected video ID
            thumbnail_editor_container.find(`#eol-update-${html_id}`).attr('data-videoid', e.target.value);

            // Update the hidden video_id filed with the selected video ID and trigger a change event
            video_id_container.find('input').val(e.target.value);
            video_id_container.find('input').trigger('change');

            // Update the video URL field with the selected video ID and trigger a change event
            video_url_input.trigger('change');
            const video_url_input_val = video_url_input.val();
            
            // save video url in model level
            transcripts.settingsView.views.video_url.model.attributes.value = [video_url_input_val];
            transcripts.settingsView.views.video_url.model.attributes.explicitly_set = true;
            transcripts.settingsView.views.video_url.model.changed.value = [video_url_input_val];
            transcripts.handleFieldChanged();

            const video_id_input_val = video_id_container.find('input').val();
            
            // save video id in model level
            transcripts.settingsView.views.edx_video_id.model.attributes.value = video_id_input_val;
            transcripts.settingsView.views.edx_video_id.model.attributes.explicitly_set = true;
            transcripts.settingsView.views.edx_video_id.model.changed.value = video_id_input_val;
            transcripts.handleFieldChanged();
        });

        // Add update thumbnail function
        $('#eol-update-' + html_id).bind('click', function(e) {
            $('#ui-loading-update').show();
            e.currentTarget.disabled = true;
            $.post('/eolvimeo/update_picture', {'videoid': this.dataset.videoid, 'course_id': course_id}).done(function(response) {
                if (response.result == 'success' ){
                    $('#eol-update-response').text(gettext("Update thumbnail from Vimeo"));
                }
                else {
                    $('#eol-update-response').text(gettext("There was an error updating the thumbnail."));
                }
            }).fail(function() {
                $('#eol-update-response').text(gettext("There was an error updating the thumbnail."));
            }).always(function() {
                $('#ui-loading-update').hide();
                e.currentTarget.disabled = false;
            });
        });
    }
);
