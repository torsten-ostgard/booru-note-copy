from unittest import TestCase
from unittest import mock

from defusedxml import ElementTree

from note_copy import utils


class TestYesNo(TestCase):
    @mock.patch('builtins.input')
    def test_y(self, mock_input):
        mock_input.return_value = 'y'
        self.assertTrue(utils.yes_no(''))

    @mock.patch('builtins.input')
    def test_yes(self, mock_input):
        mock_input.return_value = 'yes'
        self.assertTrue(utils.yes_no(''))

    @mock.patch('builtins.input')
    def test_n(self, mock_input):
        mock_input.return_value = 'n'
        self.assertFalse(utils.yes_no(''))

    @mock.patch('builtins.input')
    def test_no(self, mock_input):
        mock_input.return_value = 'no'
        self.assertFalse(utils.yes_no(''))

    @mock.patch('builtins.input')
    def test_invalid_input(self, mock_input):
        mock_input.side_effect = ['a', 'b', 'y']
        self.assertTrue(utils.yes_no(''))


class TestConvertXmlToDict(TestCase):
    def test_empty(self):
        root_node = ElementTree.fromstring('<data></data>')
        result = utils.convert_xml_to_dict(root_node)
        self.assertEqual({}, result)

    def test_no_children(self):
        root_node = ElementTree.fromstring('<data dataset="countries"></data>')
        result = utils.convert_xml_to_dict(root_node)
        expected_result = {'dataset': 'countries'}
        self.assertEqual(expected_result, result)

    def test_has_children(self):
        root_node = ElementTree.fromstring('''
            <data dataset="countries">
                <country
                    name="Liechtenstein"
                    gdppc="141100"
                />
                <country
                    name="Singapore"
                    gdppc="59900"
                />
            </data>
        ''')
        result = utils.convert_xml_to_dict(root_node)
        expected_result = {
            'dataset': 'countries',
            'data': [
                {
                    'name': 'Liechtenstein',
                    'gdppc': 141100
                },
                {
                    'name': 'Singapore',
                    'gdppc': 59900,
                },
            ],
        }
        self.assertEqual(expected_result, result)
