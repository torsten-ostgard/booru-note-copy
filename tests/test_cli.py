import sys
from io import StringIO
from unittest import TestCase
from unittest import mock

from note_copy import note_copy
from note_copy.cli import main


class TestMain(TestCase):
    def setUp(self):
        self.original_stderr = sys.stderr
        sys.stderr = StringIO()
        self.original_argv = sys.argv

    def tearDown(self):
        sys.stderr.close()
        sys.stderr = self.original_stderr
        sys.argv = self.original_argv

    @mock.patch('note_copy.cli.note_copy.instantiate_post')
    @mock.patch('note_copy.cli.note_copy.BooruPost.copy_notes_from_post')
    def test_source_and_destination(self, mock_copy_notes, mock_instantiate_post):
        posts = [
            note_copy.DanbooruPost(1437880),
            note_copy.GelbooruPost(1904252),
        ]
        mock_instantiate_post.side_effect = posts
        sys.argv = ['', '--source', 'd1437880', '--destination', 'g1904252']
        main()
        c = mock.call(posts[0])
        mock_copy_notes.assert_has_calls([c])

    @mock.patch('note_copy.cli.time')
    @mock.patch('builtins.open')
    @mock.patch('note_copy.cli.note_copy.instantiate_post')
    @mock.patch('note_copy.cli.note_copy.BooruPost.copy_notes_from_post')
    def test_file(self, mock_copy_notes, mock_instantiate_post, mock_open, mock_time):
        # TODO: Get more interesting post numbers for the second set
        posts = [
            note_copy.DanbooruPost(1437880),
            note_copy.GelbooruPost(1904252),
            note_copy.DanbooruPost(12345),
            note_copy.GelbooruPost(12345),
        ]
        mock_instantiate_post.side_effect = posts
        ids = 'd1437880\t g1904252\n\n\nd12345    g12345   \n'
        mock_open.return_value = StringIO(ids)
        sys.argv = ['', '--file', '/tmp/mock_file']
        main()
        copy_notes_calls = [mock.call(p) for p in posts if type(p) is note_copy.DanbooruPost]
        cooldown = note_copy.GelbooruPost.cooldown
        sleep_calls = [mock.call(cooldown), mock.call(cooldown)]
        mock_copy_notes.assert_has_calls(copy_notes_calls)
        mock_time.sleep.assert_has_calls(sleep_calls)

    def test_only_source(self):
        sys.argv = ['', '--source', 'd1437880']

        with self.assertRaises(SystemExit) as e:
            main()

        self.assertEqual(e.exception.code, 1)
        # Printing adds a newline to the message
        self.assertEqual(sys.stderr.getvalue(), 'Specify two post numbers\n')

    def test_only_destination(self):
        sys.argv = ['', '--destination', 'g1904252']

        with self.assertRaises(SystemExit) as e:
            main()

        self.assertEqual(e.exception.code, 1)
        self.assertEqual(sys.stderr.getvalue(), 'Specify two post numbers\n')

    def test_no_args(self):
        sys.argv = ['']

        with self.assertRaises(SystemExit) as e:
            main()

        self.assertEqual(e.exception.code, 1)
        self.assertEqual(sys.stderr.getvalue(), 'No post numbers or file specified\n')
