# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import six
import json
import os
import math
import logging
from django.conf import settings
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from django.contrib.auth.models import User
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator
from .vimeo_utils import (
    upload,
    add_domain_to_video,
    move_to_folder,
    get_video_vimeo,
    update_create_vimeo_model,
    get_link_video
    )
from celery import current_task, task
from lms.djangoapps.instructor_task.tasks_base import BaseInstructorTask
from lms.djangoapps.instructor_task.api_helper import submit_task
from lms.djangoapps.instructor_task.tasks_helper.runner import run_main_task, TaskProgress
from django.db import IntegrityError, transaction
from functools import partial
from time import time
from django.utils.translation import ugettext_noop
from lms.djangoapps.instructor_task.api_helper import AlreadyRunningError
from edxval.api import update_video_status

from django.core.files.storage import get_storage_class
logger = logging.getLogger(__name__)

def upload_vimeo(data, name_folder, domain, course_id):
    """
        Upload video from edxval to vimeo.
        only upload video with status 'upload_completed'
    """
    response = []
    for video in data:
        video_info = {'edxVideoId': video.get('edxVideoId'), 'status':'', 'message': '', 'vimeo_id':''}
        if video.get('status') == 'upload_completed':
            uri_video = upload(video.get('edxVideoId'), domain, course_id)
            if uri_video == 'Error':
                video_info['status'] = 'upload_failed'
                video_info['message'] = 'No se pudo subir el video a Vimeo. '
            else:
                is_added = add_domain_to_video(uri_video.split('/')[-1])
                if is_added is False:
                    video_info['message'] = video_info['message'] + 'No se pudo agregar los dominios al video en Vimeo. '
                    logger.info('{} was dont have domain'.format(uri_video))
                is_moved = move_to_folder(uri_video.split('/')[-1], name_folder)
                if is_moved is False:
                    video_info['message'] = video_info['message'] + 'No se pudo mover el video a la carpeta principal en Vimeo. '
                    logger.info('{} was not moved'.format(uri_video))
                video_data = get_video_vimeo(uri_video.split('/')[-1])
                video_info['vimeo_id'] = uri_video.split('/')[-1]
                if len(video_data) == 0 or 'upload' not in video_data or video_data['upload']['status'] == 'error':
                    video_info['status'] = 'upload_failed'
                    video_info['message'] = video_info['message'] + 'Video no se subió correctamente a Vimeo.'
                else:
                    video_info['status'] = 'vimeo_upload'
            update_video_status(video_info.get('edxVideoId'), video_info['status'])
            logger.info(
                u'VIDEOS: Video status update with id [%s], status [%s] and message [%s]',
                video_info.get('edxVideoId'),
                video_info.get('status'),
                video_info.get('message')
            )
            response.append(video_info)
        else:
            response.append(video)
    return response

@task(base=BaseInstructorTask)
def process_data(entry_id, xmodule_instance_args):
    action_name = ugettext_noop('generated')
    task_fn = partial(task_get_data, xmodule_instance_args)

    return run_main_task(entry_id, task_fn, action_name)

def task_get_data(
        _xmodule_instance_args,
        _entry_id,
        course_id,
        task_input,
        action_name):
    course_key = course_id
    user_id = task_input['user']
    start_time = time()
    task_progress = TaskProgress(action_name, 1, start_time)

    response = upload_vimeo(task_input['data'], task_input['name_folder'], task_input['domain'], course_id)
    for video in response:
        update_create_vimeo_model(video['edxVideoId'], user_id, video['status'], video['message'], str(course_id), vimeo_id=video['vimeo_id'])
    current_step = {'step': 'Uploading Video to Vimeo'}
    return task_progress.update_task_state(extra_meta=current_step)

def task_process_data(request, course_id, data, name_folder, domain):
    course_key = CourseKey.from_string(course_id)
    task_type = 'EOL_VIMEO'
    task_class = process_data
    task_input = {'course_id': course_id, 'data': data, 'user':request.user.id, 'name_folder': name_folder, 'domain': domain}
    if len(data) > 0:
        task_key = "{}_{}_{}".format(course_id, request.user.id, data[0]['edxVideoId'])
    else:
        task_key = "{}_{}_{}".format(course_id, request.user.id, 'empty')
    return submit_task(
        request,
        task_type,
        task_class,
        course_key,
        task_input,
        task_key)
