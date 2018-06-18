from unittest import TestCase
from unittest import mock

import vcr

from note_copy import note_copy

DANBOORU_TEST_AUTH = {
    'login': 'fake_user_for_note_copy_tests',
    'api_key': 'FAKE_API_KEY_FOR_NOTE_COPY_TESTS',
}
GELBOORU_TEST_AUTH = {}


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


class TestDanbooruPost(TestCase):
    def setUp(self):
        self.post = note_copy.DanbooruPost(1437880)

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

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_post_info_property.yaml')
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_post_info_property(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        result = self.post.post_info
        # Testing the full result would be cumbersome, so spot check a few key attributes
        self.assertEqual(1904252, result['id'])
        self.assertEqual('24fb40064d89da2c9549cd4f3bc2bc77', result['md5'])

    @vcr.use_cassette('fixtures/vcr_cassettes/test_gelbooru_post/test_post_info_property.yaml')
    @mock.patch('note_copy.note_copy.GelbooruPost.auth', new_callable=mock.PropertyMock)
    def test_dimensions(self, mock_auth):
        mock_auth.return_value = GELBOORU_TEST_AUTH
        expected_result = (1192, 1064)
        result = self.post.dimensions
        self.assertEqual(expected_result, result)


class TestGetValidClasses(TestCase):
    def test_all_classes(self):
        expected_result = {
            note_copy.DanbooruPost,
            note_copy.GelbooruPost,
        }
        result = note_copy.get_valid_classes()
        self.assertEqual(expected_result, set(result))
        self.assertEqual(len(expected_result), len(result))


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
