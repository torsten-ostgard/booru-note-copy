import inspect
import json
import re
import sys
import time
from abc import ABCMeta
from abc import abstractmethod
from getpass import getpass
from pathlib import Path
from urllib.parse import quote

import defusedxml.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from cached_property import cached_property

from .exceptions import NoSupportedSites
from .exceptions import UnsupportedSite
from .utils import yes_no
from .utils import convert_xml_to_dict

TAGS_TO_REMOVE = [
    'translation_request',
    'partially_translated',
    'check_translation',
]
POST_PATTERN = re.compile(r'(\D+?)(\d+)')


class Note:
    """
    A translation note on an image.
    """
    def __init__(self, x, y, width, height, body):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.body = body

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        body = self.body.replace("'", "\\'")
        return "note_copy.Note({x}, {y}, {width}, {height}, '{body}')".format(
            width=self.width,
            height=self.height,
            x=self.x,
            y=self.y,
            body=body,
        )

    def __str__(self):
        body = (self.body if len(self.body) < 30 else self.body[0:27] + '...')
        return "{width}x{height} {x},{y} {body}".format(
            width=self.width,
            height=self.height,
            x=self.x,
            y=self.y,
            body=body,
        )

    def __hash__(self):
        return hash(repr(self))


class BooruPost(metaclass=ABCMeta):
    """
    A post on a booru-style imageboard.
    """
    def __init__(self, post_id, *, mode='r', auth_dir=None):
        self.post_id = int(post_id)
        self.mode = mode
        self.auth_dir = auth_dir

    def __eq__(self, other):
        return self.domain == other.domain and self.post_id == other.post_id

    def __str__(self):
        return '{0} Post - {1}'.format(self.site_name, self.post_id)

    @cached_property
    def auth(self):
        """
        Return the information necessary to use the site as a registered user.

        The credentials for a site can theoretically be many different forms, but they will
        typically be either a username and an API key or cookie values from a requests session
        that have the username and password hash.
        :return: authentication information
        :rtype: dict[str, str]
        """
        if not self.auth_dir:
            self.auth_dir = Path.home() / '.note_copy'

        auth_file = Path(self.auth_dir) / (self.site_name.lower() + '_auth.json')

        try:
            with auth_file.open('r') as f:
                auth = json.load(f)
            return auth
        except FileNotFoundError:
            store = yes_no('Store {0} login information?'.format(self.site_name))
            auth = self.get_auth_from_input()

        if store:
            self.auth_dir.mkdir(parents=True, exist_ok=True)

            with auth_file.open('w') as f:
                json.dump(auth, f)

        return auth

    @abstractmethod
    def notes(self):
        """
        :return: all current notes attached to a post
        :rtype: list[Note]
        """
        raise NotImplementedError

    @abstractmethod
    def post_info(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self):
        """
        :return: the x and y dimensions of the full-size image
        :rtype: (int, int)
        """
        raise NotImplementedError

    @abstractmethod
    def write_note(self, note):
        """
        Create a new note on this post that is a copy of the one provided.
        :param note: the note to be copied
        :type note: Note
        """
        raise NotImplementedError

    @abstractmethod
    def update_tags(self):
        """
        Change the tags to indicate that the post is now translated.
        """
        raise NotImplementedError

    def copy_notes_from_post(self, source_post, same_size=False):
        """
        Write all notes in the source post to this post.

        By default, if the two posts have differently-sized images, it scales the notes
        proportionally.

        :param source_post: the post from which notes will be copied
        :type source_post: BooruPost
        :param same_size: whether the two images are equal in height and width
        :type same_size: bool
        """
        copied_notes = []
        for note in source_post.notes:
            if not same_size:
                note = scale_note(note, source_post.dimensions, self.dimensions)

            self.write_note(note)
            copied_notes.append(note)
            time.sleep(self.cooldown)

        self.notes = copied_notes
        self.update_tags()
        message = 'Notes successfully copied from {src_site} #{src_id} to {dest_site} #{dest_id}'
        print(message.format(
            src_site=source_post.site_name,
            src_id=source_post.post_id,
            dest_site=self.site_name,
            dest_id=self.post_id,
        ))

        # Invalidate cached properties
        del self.__dict__['post_info']


class DanbooruPost(BooruPost):
    site_name = 'Danbooru'
    short_code = 'd'
    domain = 'danbooru.donmai.us'
    base_url = 'https://' + domain
    post_url = base_url + '/posts/{post_id}.json'
    note_url = base_url + '/notes.json'
    uses_cookies = False
    cooldown = 1

    def get_auth_from_input(self):
        username = input('Username: ')
        api_key = input('API key: ')
        auth = {'login': username, 'api_key': api_key}

        return auth

    @cached_property
    def notes(self):
        notes = []
        params = {'group_by': 'note', 'search[post_id]': self.post_id}
        params.update(self.auth)
        r = requests.get(self.note_url, params=params)
        api_notes = r.json()

        for note in api_notes:
            if note['is_active']:
                notes.append(Note(
                    note['x'],
                    note['y'],
                    note['width'],
                    note['height'],
                    note['body'],
                ))

        return notes

    @cached_property
    def post_info(self):
        """
        :return: a dictionary of post metadata
        :rtype: dict[str, str]
        """
        post_url = self.post_url.format(post_id=self.post_id)
        r = requests.get(post_url, params=self.auth)
        return r.json()

    @property
    def dimensions(self):
        return int(self.post_info['image_height']), int(self.post_info['image_width'])

    def write_note(self, note):
        payload = {
            'note[post_id]': self.post_id,
            'note[x]': note.x,
            'note[y]': note.y,
            'note[width]': note.width,
            'note[height]': note.height,
            'note[body]': note.body,
        }
        requests.post(self.note_url, data=payload, params=self.auth)

    def update_tags(self):
        tag_string = change_tags(self.post_info['tag_string'])
        payload = {'post[tag_string]': tag_string}
        post_url = self.post_url.format(post_id=self.post_id)
        requests.put(post_url, data=payload, params=self.auth)


class GelbooruPost(BooruPost):
    site_name = 'Gelbooru'
    short_code = 'g'
    domain = 'gelbooru.com'
    base_url = 'https://' + domain
    login_url = base_url + '/index.php?page=account&s=login&code=00'
    api_post_url = base_url + '/index.php?page=dapi&s=post&q=index&id={post_id}'
    html_post_url = base_url + '/index.php?page=post&s=view&id={post_id}'
    # Not all API calls support JSON and those that do are often incomplete, so just use XML
    note_url = base_url + '/index.php?page=dapi&s=note&q=index&post_id={post_id}'
    cooldown = 15  # Actual cooldown is 10 seconds, but give it a lot of wiggle room
    read_auth_keys = {'user_id', 'api_key'}
    write_auth_keys = {'user_id', 'pass_hash'}

    @property
    def read_auth(self):
        filtered_items = {k: v for k, v in self.auth.items() if k in self.read_auth_keys}
        return filtered_items

    @property
    def write_auth(self):
        filtered_items = {k: v for k, v in self.auth.items() if k in self.write_auth_keys}
        return filtered_items

    def get_auth_from_input(self):
        username = input('Username: ')
        password = getpass('Password: ')
        api_key = input('API key: ')

        session = self._login(username, password)
        cookies = requests.utils.dict_from_cookiejar(session.cookies)
        auth = {key: cookies[key] for key in self.write_auth_keys}
        auth['api_key'] = api_key

        return auth

    def _login(self, username, password):
        session = requests.session()
        payload = {'user': username, 'pass': password, 'submit': 'Log in'}
        session.post(self.login_url, data=payload)

        return session

    @cached_property
    def post_info(self):
        """
        :return: a dictionary of post metadata
        :rtype: dict[str, str|int]
        """
        if self.mode == 'r':
            return self._get_post_info_from_api()
        elif self.mode == 'w':
            return self._get_post_info_from_html()
        else:
            raise ValueError("invalid mode: '{mode}'".format(mode=self.mode))

    def _get_post_info_from_api(self):
        post_url = self.api_post_url.format(post_id=self.post_id)
        r = requests.get(post_url, params=self.read_auth)
        root = ET.fromstring(r.text)
        d = convert_xml_to_dict(root)

        return d['posts'][0]

    def _get_post_info_from_html(self):
        # Gelbooru's API is read-only, so to create or modify a resource, requests need to act
        # like a web browser. Part of this process involves using a CSRF token, which is only
        # provided in the HTML, so scraping the site is the only option.
        post_url = self.html_post_url.format(post_id=self.post_id)
        r = requests.get(post_url, cookies=self.write_auth)
        soup = BeautifulSoup(r.text, 'html.parser')
        names = ['title', 'source', 'uid', 'uname', 'csrf-token']
        post_info = {name: soup.find(attrs={'name': name}).attrs['value'] for name in names}
        rating = soup.find(attrs={'name': 'rating', 'checked': 'checked'}).attrs['value']
        post_info['rating'] = rating
        post_info['tags'] = soup.find(attrs={'id': 'tags'}).text
        # change is the key used in the API response instead of lupdated.
        post_info['change'] = soup.find(attrs={'name': 'lupdated'}).attrs['value']
        img_attrs = soup.find('img', attrs={'id': 'image'}).attrs
        post_info['height'] = int(img_attrs['data-original-height'])
        post_info['width'] = int(img_attrs['data-original-width'])
        post_info['PHPSESSID'] = r.cookies['PHPSESSID']

        return post_info

    @property
    def dimensions(self):
        return self.post_info['height'], self.post_info['width']

    @cached_property
    def notes(self):
        self.note_url = self.note_url.format(post_id=self.post_id)
        notes = []
        r = requests.get(self.note_url, params=self.read_auth)
        root = ET.fromstring(r.text)
        d = convert_xml_to_dict(root)
        api_notes = d.get('notes', [])

        for note in api_notes:
            body = note['body'].replace('<br />', '\n')
            notes.append(Note(
                note['x'],
                note['y'],
                note['width'],
                note['height'],
                body,
            ))

        return notes

    def write_note(self, note):
        payload = {
            'note[html_id]': 'x',
            'note[x]': note.x,
            'note[y]': note.y,
            'note[width]': note.width,
            'note[height]': note.height,
            'note[body]': quote(note.body),
            'note[post_id]': self.post_id,
        }
        url = self.base_url + '/public/note_save.php?id=-2'
        requests.post(url, data=payload, cookies=self.write_auth)

    def update_tags(self):
        rating = self.post_info['rating']
        # None is an invalid value for Gelbooru, so make the title an empty string if not found
        title = self.post_info.get('title', '')
        source = self.post_info['source']
        tag_string = change_tags(self.post_info['tags'])
        pconf = '1'
        lupdated = self.post_info['change']
        submit = 'Save changes'

        payload = {
            'rating': rating,
            'title': title,
            'source': source,
            'tags': tag_string,
            'id': self.post_id,
            'uid':  self.post_info['uid'],
            'uname': self.post_info['uname'],
            'pconf': pconf,
            'lupdated': lupdated,
            'csrf-token': self.post_info['csrf-token'],
            'submit': submit,
        }
        url = self.base_url + '/public/edit_post.php'
        cookies = {'PHPSESSID': self.post_info['PHPSESSID'], **self.write_auth}
        requests.post(url, data=payload, cookies=cookies)


def get_valid_classes():
    """
    :return: a set of classes representing the sites supported by this script
    :rtype: set[BooruPost]
    """
    classes = [cls[1] for cls in inspect.getmembers(sys.modules[__name__], inspect.isclass)]
    valid_classes = set()

    for cls in classes:
        if issubclass(cls, BooruPost):
            try:
                # Ensure that only implemented classes get returned
                cls.domain
                valid_classes.add(cls)
            except AttributeError:
                continue

    return valid_classes


def instantiate_post(valid_classes, post_string, mode='r'):
    """
    Create a BooruPost object from a string

    The string representing the post should be in one of the following forms:
        e12345 (where 'e' is abreviation for the site)
        example.com12345 (where example.com is the full domain name)

    :param valid_classes: classes representing the supported sites
    :type valid_classes: list of BooruPost classes
    :param post_string: the site code and post number of the post to instantiated
    :type post_string: str
    :return: an object representing the given post
    :rtype: BooruPost
    """
    if not valid_classes:
        raise NoSupportedSites()

    matches = re.search(POST_PATTERN, post_string)
    site_identifier, post_id = matches.groups()

    for cls in valid_classes:
        if site_identifier.lower() in {cls.short_code, cls.domain}:
            return cls(post_id, mode=mode)

    raise UnsupportedSite('No supported site found for identifier: ' + site_identifier)


def scale_note(source_note, source_dimensions, destination_dimensions):
    """
    Transforms a note to be proportional to the destination image.

    :return: a new note
    :rtype: Note
    """
    image_width, image_height = destination_dimensions
    source_image_width, source_image_height = source_dimensions
    x_ratio = image_width / source_image_width
    y_ratio = image_height / source_image_height
    scaled_width = source_note.width * x_ratio
    scaled_height = source_note.height * y_ratio
    scaled_x = source_note.x * x_ratio
    scaled_y = source_note.y * y_ratio

    return Note(scaled_x, scaled_y, scaled_width, scaled_height, source_note.body)


def change_tags(tag_string):
    """
    Remove tags indicating that an image is untranslated and add the translated tag

    :param tag_string: space-delimited list of tags
    :type tag_string: str
    :return: the modified tag string
    :rtype: str
    """
    for tag in TAGS_TO_REMOVE:
        tag_string = tag_string.replace(tag, '')

    tag_string += ' translated'
    return tag_string
