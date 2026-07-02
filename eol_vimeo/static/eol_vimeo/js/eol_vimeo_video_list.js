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
        
        const editor_container = transcripts.$el
        
        // get youtube url li
        const li_youtube_url = transcripts.settingsView.views.video_url.$el
        // update  youtube_url label
        li_youtube_url.find('.metadata-videolist-enum label').text(gettext("External link from YouTube (default video URL)"));

        // get 
        const li_video_id = transcripts.settingsView.views.edx_video_id.$el
        // hide video_id li element
        li_video_id.hide();

        // create video select
        editor_container.find('ul.list-input.settings-list').prepend(`
            <li class="field comp-setting-entry metadata_entry">
                <div class="wrapper-comp-setting">
                <label class="label setting-label">${gettext("Select a video")}</label>
                    <select id="eol-video-${html_id}">
                    </select>
                    <span class="tip setting-help">
                        ${gettext("Select a video previously uploaded to the course or insert an external YouTube link in the corresponding field.")}
                    </span>
                </div>
            </li>
        `);
        
        var pre_exists_video_id = true;
        // Create video options
        eol_video_list.forEach(video => {
            const isSelected = video.edx_video_id === edx_selected_video_id;
            if (isSelected) {
                pre_exists_video_id = false;
            }
            $(`#eol-video-${html_id}`).append(
                $('<option>', {
                    value: video.edx_video_id,
                    selected: isSelected
                }).text(video.display_name)
            );
        });
        // create default video option
        $(`#eol-video-${html_id}`).prepend(
            `<option value="" ${pre_exists_video_id ? 'selected' : ''}>
                ${gettext("External YouTube link")}
            </option>`
        );

        // create html thumbnail start as hide
        update_thumbnail_html = `
        <li class="field comp-setting-entry metadata_entry update-thumbnail-vimeo">
            <div class="wrapper-comp-setting">
                <label class="label setting-label">${gettext("Update thumbnail from Vimeo")}</label>
                <button id="eol-update-${html_id}" class="action setting-upload update-vimeo" type="button" data-tooltip="${gettext("Update")}" data-videoid="${edx_selected_video_id}" value="${gettext("Update")}">${gettext("Update")}</button>
            </div>
            <span class="tip setting-help">
                <div id="ui-loading-update" class="ui-loading is-hidden">
                    <p>
                        <span class="spin"><span class="icon fa fa-refresh" aria-hidden="true"></span></span>
                        <span class="copy">${gettext("Updating")}</span>
                    </p>
                </div>
            </span>
            <span id="eol-update-response" class="tip setting-help"></span>
        </li>
        `   
        // add thumbnail picture
        editor_container.find('ul.list-input.settings-list').append(update_thumbnail_html);

        const thumbnail_video_update = editor_container.find('.update-thumbnail-vimeo')
        // hide update thumbnail button and show youtube url link
        if (pre_exists_video_id){
            li_youtube_url.find('.metadata-videolist-enum').show();
            thumbnail_video_update.hide();
        }
        // show update thumbnail button and hide youtube url link
        else{
            li_youtube_url.find('.metadata-videolist-enum').hide();
            thumbnail_video_update.show();
        }

        // Detect change in video_id or select
        $('#eol-video-' + html_id).on('change', function(e) {
            const youtube_input = li_youtube_url.find('.metadata-videolist-enum input')
            youtube_input.val('');

            if (e.target.value != ""){
                li_youtube_url.find('.metadata-videolist-enum').hide();
                thumbnail_video_update.show();
                
                // Set the data-videoid attribute of the hidden field to the selected video ID
                thumbnail_video_update.find(`#eol-update-${html_id}`).attr('data-videoid', e.target.value);
            }
            else{
                li_youtube_url.find('.metadata-videolist-enum').show();
                thumbnail_video_update.hide();
                thumbnail_video_update.find(`#eol-update-${html_id}`).attr('data-videoid', '');
            }

            // Update the hidden video_id filed with the selected video ID and trigger a change event
            li_video_id.find('input').val(e.target.value);
            li_video_id.find('input').trigger('change');

            // Update the video URL field with the selected video ID and trigger a change event
            youtube_input.trigger('change');
            youtube_external_input_val = youtube_input.val();
            
            // save youtube url in model level
            transcripts.settingsView.views.video_url.model.attributes.value = [youtube_external_input_val];
            transcripts.settingsView.views.video_url.model.attributes.explicitly_set = true;
            transcripts.settingsView.views.video_url.model.changed.value = [youtube_external_input_val];
            transcripts.handleFieldChanged();
        });

        // Add update thumbnail function
        $('#eol-update-' + html_id).bind('click', function(e) {
            editor_container.find('#ui-loading-update').show();
            e.currentTarget.disabled = true;
            $.post('/eolvimeo/update_picture', {'videoid': this.dataset.videoid, 'course_id': course_id}).done(function(response) {
                if (response.result == 'success' ){
                    text_response = editor_container.find('#eol-update-response');
                    text_response.html(gettext("Updated miniature."));
                }
                else {
                    text_response = editor_container.find('#eol-update-response');
                    text_response.html(gettext("There was an error updating the thumbnail."));
                }
                editor_container.find('#ui-loading-update').hide();
                e.currentTarget.disabled = false;
            }).fail(function() {
                text_response = editor_container.find('#eol-update-response');
                text_response.html(gettext("There was an error updating the thumbnail."));
                editor_container.find('#ui-loading-update').hide();
                e.currentTarget.disabled = false;
            });
        });
    }
);
