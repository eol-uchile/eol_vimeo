# -*- coding: utf-8 -*-
# Python Standard Libraries
from __future__ import unicode_literals
from collections import namedtuple

# Installed packages (via pip)
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch

# Edx dependencies
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

# Internal project dependencies
from . import thumbnail, vimeo_utils
from .models import EolVimeoVideo

class TestEolVimeoThumbnail(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):
        super(TestEolVimeoThumbnail, self).setUp()
        # create a course
        self.maxDiff = None
        self.course = CourseFactory.create(
            org='mss', course='999', display_name='eol_test_course')
        self.course2 = CourseFactory.create(
            org='mss', course='222', display_name='eol_test_course2')
        self.vimeo_id = '622803261'
        self.picture_url = 'https://i.vimeocdn.com/video/1234567890-abcdef-d'
        with patch('common.djangoapps.student.models.cc.User.save'):
            # staff user
            self.user = UserFactory(
                username='testuser2',
                password='12345',
                email='student2@edx.org',
                is_staff=True)

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_normal_process(self, get):
        """
            Test get_thumbnail_url normal process, the picture is saved in every row with that vimeo_video_id
        """
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            status = 'upload_completed',
            error_description = ''
        )
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course2.id,
            url_vimeo = '',
            status = 'upload_completed',
            error_description = ''
        )
        get_data = {'pictures': {'type': 'custom', 'base_link': self.picture_url}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data),]
        result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, self.picture_url)
        eolvimeo1 = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course.id)
        eolvimeo2 = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course2.id)
        self.assertEqual(eolvimeo1.url_picture, self.picture_url)
        self.assertEqual(eolvimeo2.url_picture, self.picture_url)

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_stored(self, get):
        """
            Test get_thumbnail_url when url_picture is already saved, vimeo api is not called
        """
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            url_picture = self.picture_url,
            status = 'upload_completed',
            error_description = ''
        )
        result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, self.picture_url)
        get.assert_not_called()

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_second_call(self, get):
        """
            Test get_thumbnail_url second call uses the saved url_picture, vimeo api is called only once
        """
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            status = 'upload_completed',
            error_description = ''
        )
        get_data = {'pictures': {'type': 'custom', 'base_link': self.picture_url}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data),]
        self.assertEqual(thumbnail.get_thumbnail_url(self.vimeo_id), self.picture_url)
        self.assertEqual(thumbnail.get_thumbnail_url(self.vimeo_id), self.picture_url)
        self.assertEqual(get.call_count, 1)

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_without_model(self, get):
        """
            Test get_thumbnail_url when vimeo_id is not in eolvimeo model, returns the url but nothing is saved
        """
        get_data = {'pictures': {'type': 'custom', 'base_link': self.picture_url}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data),]
        result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, self.picture_url)
        self.assertEqual(len(EolVimeoVideo.objects.all()), 0)

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_default_picture(self, get):
        """
            Test get_thumbnail_url when vimeo returns the default picture (video still processing), it is not saved
        """
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            status = 'upload_completed',
            error_description = ''
        )
        default_url = 'https://i.vimeocdn.com/video/default'
        get_data = {'pictures': {'type': 'default', 'base_link': default_url}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data),]
        result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, default_url)
        eolvimeo = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course.id)
        self.assertEqual(eolvimeo.url_picture, '')

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_without_pictures(self, get):
        """
            Test get_thumbnail_url when vimeo response has no pictures
        """
        get_data = {}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data),]
        result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, '')

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_video_not_found(self, get):
        """
            Test get_thumbnail_url when the video does not exist in vimeo
        """
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            status = 'upload_completed',
            error_description = ''
        )
        get_data = {'error': "The requested video couldn't be found."}
        get.side_effect = [namedtuple("Request", ["status_code", "json", "text"])(404, lambda:get_data, "The requested video couldn't be found."),]
        with self.assertLogs('eol_vimeo.thumbnail', level='INFO') as cm:
            result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, '')
        self.assertTrue(any(
        'EolVimeo - Thumbnail, vimeo_id: {}, status: 404'.format(self.vimeo_id) in log
        for log in cm.output))
        eolvimeo = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course.id)
        self.assertEqual(eolvimeo.url_picture, '')

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_exception(self, get):
        """
            Test get_thumbnail_url with exception error
        """
        get.side_effect = Exception("Test error")
        with self.assertLogs('eol_vimeo.thumbnail', level='INFO') as cm:
            result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, '')
        self.assertTrue(any(
        'EolVimeo - Thumbnail, exception vimeo_id: {}, error: Test error'.format(self.vimeo_id) in log
        for log in cm.output))

    @override_settings(EOL_VIMEO_CLIENT_ID='')
    def test_get_thumbnail_url_no_credentials(self):
        """
            Test get_thumbnail_url when credentials are not defined
        """
        result = thumbnail.get_thumbnail_url(self.vimeo_id)
        self.assertEqual(result, '')

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_force(self, get):
        """
            Test get_thumbnail_url with force=True skips the saved url_picture, calls vimeo api and overwrites it
        """
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            url_picture = 'https://i.vimeocdn.com/video/old-picture',
            status = 'upload_completed',
            error_description = ''
        )
        get_data = {'pictures': {'type': 'custom', 'base_link': self.picture_url}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data),]
        result = thumbnail.get_thumbnail_url(self.vimeo_id, force=True)
        self.assertEqual(result, self.picture_url)
        self.assertEqual(get.call_count, 1)
        eolvimeo = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course.id)
        self.assertEqual(eolvimeo.url_picture, self.picture_url)

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_get_thumbnail_url_force_default_picture(self, get):
        """
            Test get_thumbnail_url with force=True when vimeo returns the default picture, the saved url_picture is kept
        """
        old_picture = 'https://i.vimeocdn.com/video/old-picture'
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            url_picture = old_picture,
            status = 'upload_completed',
            error_description = ''
        )
        get_data = {'pictures': {'type': 'default', 'base_link': 'https://i.vimeocdn.com/video/default'}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data),]
        thumbnail.get_thumbnail_url(self.vimeo_id, force=True)
        eolvimeo = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course.id)
        self.assertEqual(eolvimeo.url_picture, old_picture)

    @patch('requests.get')
    def test_get_thumbnail_url_empty_vimeo_id(self, get):
        """
            Test get_thumbnail_url with empty vimeo_id, vimeo api is not called
        """
        self.assertEqual(thumbnail.get_thumbnail_url(''), '')
        self.assertEqual(thumbnail.get_thumbnail_url(None), '')
        get.assert_not_called()

class TestEolVimeoThumbnailView(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):
        super(TestEolVimeoThumbnailView, self).setUp()
        # create a course
        self.course = CourseFactory.create(
            org='mss', course='999', display_name='eol_test_course')
        self.vimeo_id = '622803261'
        self.picture_url = 'https://i.vimeocdn.com/video/1234567890-abcdef-d'
        self.client = Client()
        self.client3 = Client()
        with patch('common.djangoapps.student.models.cc.User.save'):
            # staff user
            self.user = UserFactory(
                username='testuser2',
                password='12345',
                email='student2@edx.org',
                is_staff=True)
            self.client.login(username='testuser2', password='12345')
            self.student_user = UserFactory(
                username='student_user',
                password='12345',
                email='student_test@edx.org')
            self.client3.login(username='student_user', password='12345')
        EolVimeoVideo.objects.create(
            edx_video_id = '123-456-789',
            user =self.user,
            vimeo_video_id = self.vimeo_id,
            course_key = self.course.id,
            url_vimeo = '',
            status = 'upload_completed',
            error_description = ''
        )

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_vimeo_thumbnail(self, get):
        """
            Test vimeo_thumbnail normal process
        """
        get_data = {'pictures': {'type': 'custom', 'base_link': self.picture_url}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data)]
        result = self.client.get(
            reverse('vimeo_thumbnail', kwargs={'vimeo_id': self.vimeo_id}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {'thumbnail_url': self.picture_url})
        eolvimeo = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course.id)
        self.assertEqual(eolvimeo.url_picture, self.picture_url)

    @patch('requests.get')
    def test_vimeo_thumbnail_student_user(self, get):
        """
            Test vimeo_thumbnail when user is student and url_picture is already saved
        """
        EolVimeoVideo.objects.filter(vimeo_video_id=self.vimeo_id).update(url_picture=self.picture_url)
        result = self.client3.get(
            reverse('vimeo_thumbnail', kwargs={'vimeo_id': self.vimeo_id}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {'thumbnail_url': self.picture_url})
        get.assert_not_called()

    @override_settings(EOL_VIMEO_CLIENT_ID='')
    def test_vimeo_thumbnail_without_picture(self):
        """
            Test vimeo_thumbnail when there is no picture and credentials are not defined
        """
        result = self.client.get(
            reverse('vimeo_thumbnail', kwargs={'vimeo_id': self.vimeo_id}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {'thumbnail_url': ''})

    def test_vimeo_thumbnail_annonimous_user(self):
        """
            Test vimeo_thumbnail when user is annonimous
        """
        client = Client()
        result = client.get(
            reverse('vimeo_thumbnail', kwargs={'vimeo_id': self.vimeo_id}))
        self.assertEqual(result.status_code, 401)

    def test_vimeo_thumbnail_wrong_vimeo_id(self):
        """
            Test vimeo_thumbnail when vimeo_id is not numeric
        """
        result = self.client.get('/eolvimeo/thumbnail/abc')
        self.assertEqual(result.status_code, 404)

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_vimeo_thumbnail_post_force(self, get):
        """
            Test vimeo_thumbnail POST forces the refresh from vimeo even if url_picture is already saved
        """
        EolVimeoVideo.objects.filter(vimeo_video_id=self.vimeo_id).update(url_picture='https://i.vimeocdn.com/video/old-picture')
        get_data = {'pictures': {'type': 'custom', 'base_link': self.picture_url}}
        get.side_effect = [namedtuple("Request", ["status_code", "json"])(200, lambda:get_data)]
        result = self.client3.post(
            reverse('vimeo_thumbnail', kwargs={'vimeo_id': self.vimeo_id}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {'thumbnail_url': self.picture_url})
        self.assertEqual(get.call_count, 1)
        eolvimeo = EolVimeoVideo.objects.get(vimeo_video_id=self.vimeo_id, course_key=self.course.id)
        self.assertEqual(eolvimeo.url_picture, self.picture_url)

    @patch('requests.get')
    @override_settings(EOL_VIMEO_CLIENT_ID='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_SECRET='1234567890asdfgh')
    @override_settings(EOL_VIMEO_CLIENT_TOKEN='1234567890asdfgh')
    def test_vimeo_thumbnail_post_error(self, get):
        """
            Test vimeo_thumbnail POST when vimeo api fails, returns empty thumbnail_url
        """
        get_data = {'error': "The requested video couldn't be found."}
        get.side_effect = [namedtuple("Request", ["status_code", "json", "text"])(404, lambda:get_data, "The requested video couldn't be found."),]
        result = self.client.post(
            reverse('vimeo_thumbnail', kwargs={'vimeo_id': self.vimeo_id}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {'thumbnail_url': ''})

    @patch('requests.get')
    def test_vimeo_thumbnail_post_annonimous_user(self, get):
        """
            Test vimeo_thumbnail POST when user is annonimous, vimeo api is not called
        """
        client = Client()
        result = client.post(
            reverse('vimeo_thumbnail', kwargs={'vimeo_id': self.vimeo_id}))
        self.assertEqual(result.status_code, 401)
        get.assert_not_called()
