import json
import shutil
from pathlib import Path
from tempfile import mkdtemp
from unittest import TestCase
from unittest import mock

import requests
import vcr

from note_copy import exceptions
from note_copy import note_copy

DANBOORU_TEST_AUTH = {
    'login': 'fake_user_for_note_copy_tests',
    'api_key': 'FAKE_API_KEY_FOR_NOTE_COPY_TESTS',
}
GELBOORU_TEST_AUTH = {
    'user_id': '1648',
    'pass_hash': '80c1ed9c72b4d7048851a6a6d629ba4abe5e8c76',
    'api_key': 'FAKE_API_KEY_FOR_NOTE_COPY_TESTS',
}


class TestNote(TestCase):
    def test_int_params(self):
        result = note_copy.Note(1, 2, 3, 4, 'test')
        self.assertEqual(1, result.x)
        self.assertEqual(2, result.y)
        self.assertEqual(3, result.width)
        self.assertEqual(4, result.height)
        self.assertEqual('test', result.body)

    def test_str_params(self):
        expected_result = note_copy.Note(1, 2, 3, 4, 'test')
        result = note_copy.Note('1', '2', '3', '4', 'test')
        self.assertEqual(expected_result, result)

    def test_str(self):
        expected_result = '3x4 1,2 test'
        result = str(note_copy.Note(1, 2, 3, 4, 'test'))
        self.assertEqual(expected_result, result)

    def test_str_with_long_body(self):
        expected_result = '3x4 1,2 abcdefghijklmnopqrstuvwxyz1...'
        result = str(note_copy.Note(1, 2, 3, 4, 'abcdefghijklmnopqrstuvwxyz1234567890'))
        self.assertEqual(expected_result, result)

    def test_str_with_long_body_below_limit(self):
        expected_result = '3x4 1,2 abcdefghijklmnopqrstuvwxyz123'
        result = str(note_copy.Note(1, 2, 3, 4, 'abcdefghijklmnopqrstuvwxyz123'))
        self.assertEqual(expected_result, result)

    def test_repr(self):
        note = note_copy.Note(1, 2, 3, 4, '"I swear I don\'t even"')
        self.assertEqual(note, eval(repr(note)))


class TestScaleNote(TestCase):
    def test_scale_note(self):
        note = note_copy.Note(1, 2, 30, 40, 'test')
        source_dimensions = (100, 200)
        destination_dimensions = (300, 400)
        result = note_copy.scale_note(note, source_dimensions, destination_dimensions)
        expected_result = note_copy.Note(3, 4, 90, 80, 'test')
        self.assertEqual(expected_result, result)


class TestBooruPost(TestCase):
    def test_equality_does_match(self):
        danbooru_post_1 = note_copy.DanbooruPost(1234)
        # Simulate note being fetched
        danbooru_post_1.notes = [note_copy.Note(1, 2, 3, 4, 'test')]
        danbooru_post_2 = note_copy.DanbooruPost('1234')
        self.assertEqual(danbooru_post_1, danbooru_post_2)

    def test_equality_does_not_match(self):
        danbooru_post = note_copy.DanbooruPost(1234)
        gelbooru_post = note_copy.GelbooruPost(1234)
        self.assertNotEqual(danbooru_post, gelbooru_post)

    @mock.patch('note_copy.note_copy.getpass')
    @mock.patch('note_copy.note_copy.input')
    @mock.patch('note_copy.note_copy.yes_no')
    @mock.patch('note_copy.note_copy.Path.home')
    def test_auth_stores_credentials(self, mock_home, mock_yes_no, mock_input, mock_getpass):
        tmp_dir = mkdtemp()
        mock_home.return_value = Path(tmp_dir)
        mock_yes_no.return_value = True
        mock_input.side_effect = [
            'fake_user_for_note_copy_tests',
            'FAKE_API_KEY_FOR_NOTE_COPY_TESTS',
            'fake_user_for_note_copy_tests',
            'FAKE_API_KEY_FOR_NOTE_COPY_TESTS',
        ]
        mock_getpass.return_value = 'fake_password'
        session = mock.Mock()
        jar = requests.cookies.RequestsCookieJar()
        jar.set('user_id', '1648')
        jar.set('pass_hash', '80c1ed9c72b4d7048851a6a6d629ba4abe5e8c76')
        session.cookies = jar

        def mock_login(username, auth_string):
            return session

        danbooru_post = note_copy.DanbooruPost(1234)
        gelbooru_post = note_copy.GelbooruPost(1234)
        gelbooru_post._login = mock_login

        danbooru_auth = danbooru_post.auth
        gelbooru_auth = gelbooru_post.auth

        self.assertEqual(danbooru_auth, DANBOORU_TEST_AUTH)
        self.assertEqual(gelbooru_auth, GELBOORU_TEST_AUTH)
        danbooru_auth_file = Path(tmp_dir) / '.note_copy' / 'danbooru_auth.json'
        gelbooru_auth_file = Path(tmp_dir) / '.note_copy' / 'gelbooru_auth.json'

        with danbooru_auth_file.open('r') as f:
            self.assertEqual(json.load(f), DANBOORU_TEST_AUTH)

        with gelbooru_auth_file.open('r') as f:
            self.assertEqual(json.load(f), GELBOORU_TEST_AUTH)

        shutil.rmtree(tmp_dir)

    def test_str(self):
        danbooru_post = note_copy.DanbooruPost(1234)
        gelbooru_post = note_copy.GelbooruPost(1234)
        self.assertEqual(str(danbooru_post), 'Danbooru Post - 1234')
        self.assertEqual(str(gelbooru_post), 'Gelbooru Post - 1234')


class TestDanbooruPost(TestCase):
    def setUp(self):
        self.post = note_copy.DanbooruPost(1437880)

    @mock.patch('note_copy.note_copy.input')
    @mock.patch('note_copy.note_copy.yes_no')
    def test_auth(self, mock_yes_no, mock_input):
        self.post.auth_dir = Path('does_not_exist')
        mock_yes_no.return_value = False
        mock_input.side_effect = [
            'fake_user_for_note_copy_tests',
            'FAKE_API_KEY_FOR_NOTE_COPY_TESTS',
        ]
        result = self.post.auth
        self.assertEqual(result, DANBOORU_TEST_AUTH)

    def test_stored_auth(self):
        self.post.auth_dir = Path('fixtures') / 'auth'
        result = self.post.auth
        self.assertEqual(result, DANBOORU_TEST_AUTH)

    # When using VCR tapes, be VERY careful to not commit sensitive information like API keys,
    # session cookies, password hashes, etc.
    @vcr.use_cassette('fixtures/vcr_cassettes/test_danbooru_post/test_notes_property.yaml')
    @mock.patch('note_copy.note_copy.DanbooruPost.auth', new_callable=mock.PropertyMock)
    def test_notes_property(self, mock_auth):
        mock_auth.return_value = DANBOORU_TEST_AUTH
        expected_result = [
            note_copy.Note(187, 879, 40, 95, 'Tights'),
            note_copy.Note(223, 17, 217, 55, 'Hirasawa U&I'),
        ]
        result = self.post.notes
        self.assertEqual(expected_result, result)

    @vcr.use_cassette('fixtures/vcr_cassettes/test_danbooru_post/test_post_info_property.yaml')
    @mock.patch('note_copy.note_copy.DanbooruPost.auth', new_callable=mock.PropertyMock)
    def test_post_info_property(self, mock_auth):
        mock_auth.return_value = DANBOORU_TEST_AUTH
        result = self.post.post_info
        # Testing the full result would be cumbersome, so spot check a few key attributes
        self.assertEqual(1437880, result['id'])
        self.assertEqual('24fb40064d89da2c9549cd4f3bc2bc77', result['md5'])

    @vcr.use_cassette('fixtures/vcr_cassettes/test_danbooru_post/test_post_info_property.yaml')
    @mock.patch('note_copy.note_copy.DanbooruPost.auth', new_callable=mock.PropertyMock)
    def test_dimensions(self, mock_auth):
        mock_auth.return_value = DANBOORU_TEST_AUTH
        expected_result = (1192, 1064)
        result = self.post.dimensions
        self.assertEqual(expected_result, result)


class TestGelbooruPost(TestCase):
    def setUp(self):
        self.post = note_copy.GelbooruPost(1904252)

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_auth.yaml')
    @mock.patch('note_copy.note_copy.getpass')
    @mock.patch('note_copy.note_copy.input')
    @mock.patch('note_copy.note_copy.yes_no')
    def test_auth(self, mock_yes_no, mock_input, mock_getpass):
        self.post.auth_dir = Path('does_not_exist')
        mock_yes_no.return_value = False
        mock_input.side_effect = [
            'fake_user_for_note_copy_tests',
            'FAKE_API_KEY_FOR_NOTE_COPY_TESTS',
        ]
        mock_getpass.return_value = 'fake_password'
        result = self.post.auth
        self.assertEqual(result, GELBOORU_TEST_AUTH)

    def test_stored_auth(self):
        self.post.auth_dir = Path('fixtures') / 'auth'
        result = self.post.auth
        self.assertEqual(result, GELBOORU_TEST_AUTH)

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_notes_property.yaml')
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_notes_property(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        expected_result = [
            note_copy.Note(223, 17, 217, 55, 'Hirasawa U&I'),
            note_copy.Note(187, 879, 40, 95, 'Tights'),
        ]
        result = self.post.notes
        self.assertEqual(expected_result, result)

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_notes_property_no_notes.yaml')
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_notes_property_no_notes(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        result = self.post.notes
        self.assertEqual([], result)

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_post_info_property_read.yaml')
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_post_info_property_read(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        result = self.post.post_info
        # Testing the full result would be cumbersome, so spot check a few key attributes
        self.assertEqual(1904252, result['id'])
        self.assertEqual('24fb40064d89da2c9549cd4f3bc2bc77', result['md5'])

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_post_info_property_write.yaml')  # noqa: E501
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_post_info_property_write(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        post = note_copy.GelbooruPost(1904252, mode='w')
        result = post.post_info
        # Testing the full result would be cumbersome, so spot check a few key attributes
        self.assertEqual(
            '7a80127b5b02efa74c37332351d88ebe309f57afee6deebf4745e9d44545fd05',
            result['csrf-token'],
        )
        self.assertEqual('pbdnlog5di3ki2mr9b1odombh0', result['PHPSESSID'])

    def test_post_info_invalid_mode(self):
        post = note_copy.GelbooruPost(1904252, mode='rw')

        with self.assertRaises(ValueError):
            post.post_info

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_post_info_property_read.yaml')
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_dimensions_read(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        expected_result = (1192, 1064)
        result = self.post.dimensions
        self.assertEqual(expected_result, result)

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_post_info_property_write.yaml')  # noqa: E501
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_dimensions_write(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        post = note_copy.GelbooruPost(1904252, mode='w')
        expected_result = (1192, 1064)
        result = post.dimensions
        self.assertEqual(expected_result, result)


class TestGetValidClasses(TestCase):
    def test_all_classes(self):
        expected_result = {
            note_copy.DanbooruPost,
            note_copy.GelbooruPost,
        }
        result = note_copy.get_valid_classes()
        self.assertEqual(expected_result, result)


class TestInstantiatePost(TestCase):
    def setUp(self):
        self.valid_classes = {
            note_copy.DanbooruPost,
            note_copy.GelbooruPost,
        }

    def test_no_sites(self):
        with self.assertRaises(exceptions.NoSupportedSites):
            note_copy.instantiate_post([], 'd1437880')

    def test_unsupported_site(self):
        with self.assertRaises(exceptions.UnsupportedSite):
            note_copy.instantiate_post(self.valid_classes, 'example.com1437880')

    def test_short_code(self):
        expected_result = note_copy.DanbooruPost(1437880)
        result = note_copy.instantiate_post(self.valid_classes, 'd1437880')
        self.assertEqual(expected_result, result)

    def test_domain(self):
        expected_result = note_copy.DanbooruPost(1437880)
        result = note_copy.instantiate_post(self.valid_classes, 'danbooru.donmai.us1437880')
        self.assertEqual(expected_result, result)


class TestChangeTags(TestCase):
    def test_empty(self):
        result = note_copy.change_tags('')
        self.assertEqual(' translated', result)

    def test_no_tags_to_remove(self):
        tag_string = '1girl absurdres apron bag bench'
        expected_result = '1girl absurdres apron bag bench translated'
        result = note_copy.change_tags(tag_string)
        self.assertEqual(expected_result, result)

    def test_only_tags_to_remove(self):
        tag_string = ' '.join(note_copy.TAGS_TO_REMOVE)
        expected_result = ' ' * (len(note_copy.TAGS_TO_REMOVE) - 1) + ' translated'
        result = note_copy.change_tags(tag_string)
        self.assertEqual(expected_result, result)

    def test_normal_string(self):
        tag_string = (
            '1girl absurdres apron bag bench translation_request brown_eyes brown_hair goto_p ' +
            'guitar_case highres hirasawa_ui huge_filesize instrument_case k-on! ladle ponytail ' +
            'school_bag solo'
        )
        expected_result = (
            '1girl absurdres apron bag bench  brown_eyes brown_hair goto_p guitar_case highres ' +
            'hirasawa_ui huge_filesize instrument_case k-on! ladle ponytail school_bag solo ' +
            'translated'
        )
        result = note_copy.change_tags(tag_string)
        self.assertEqual(expected_result, result)


class TestIntegration(TestCase):
    @vcr.use_cassette('fixtures/vcr_cassettes/test_copy_notes/test_copy_notes_from_d_to_g.yaml')
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    @mock.patch('note_copy.note_copy.DanbooruPost.auth', new_callable=mock.PropertyMock)
    @mock.patch('note_copy.note_copy.time.sleep')
    def test_copy_notes_from_d_to_g(self, mock_sleep, mock_danbooru_auth, mock_gelbooru_auth):
        mock_danbooru_auth.return_value = DANBOORU_TEST_AUTH
        mock_gelbooru_auth.return_value = GELBOORU_TEST_AUTH
        # If a new integration test needs to be recorded, unmock sleep and auth calls
        danbooru_post = note_copy.DanbooruPost(284392)
        gelbooru_post = note_copy.GelbooruPost(302738, mode='w')
        gelbooru_post.copy_notes_from_post(danbooru_post)
        self.assertEqual(set(danbooru_post.notes), set(gelbooru_post.notes))
