import sys
from unittest import TestCase
from unittest import mock

from six import StringIO

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

    @mock.patch('note_copy.cli.note_copy.copy_notes')
    def test_source_and_destination(self, mock_copy_notes):
        sys.argv = ['', '--source', 'd1437880', '--destination', 'g1904252']
        main()
        valid_classes = {note_copy.DanbooruPost, note_copy.GelbooruPost}
        c = mock.call(valid_classes, 'd1437880', 'g1904252')
        mock_copy_notes.assert_has_calls([c])

    @mock.patch('note_copy.cli.time')
    @mock.patch('note_copy.cli.open')
    @mock.patch('note_copy.cli.note_copy.copy_notes')
    def test_file(self, mock_copy_notes, mock_open, mock_time):
        # TODO: Get more interesting post numbers for the second set
        ids = 'd1437880\t g1904252\n\n\nd12345    g12345   \n'
        mock_open.return_value = StringIO(ids)
        sys.argv = ['', '--file', '/tmp/mock_file']
        main()
        valid_classes = {note_copy.DanbooruPost, note_copy.GelbooruPost}
        copy_notes_calls = [
            mock.call(valid_classes, 'd1437880', 'g1904252'),
            mock.call(valid_classes, 'd12345', 'g12345'),
        ]
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
