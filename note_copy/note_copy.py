from __future__ import print_function

import getpass
import inspect
import os
import pickle
import re
import sys
import time
from abc import ABCMeta
from abc import abstractmethod

import defusedxml.ElementTree as ET
import requests
from cached_property import cached_property
from six import add_metaclass
from six.moves import input
from six.moves.urllib.parse import quote

from .utils import yes_no
from .utils import convert_xml_to_dict

TAGS_TO_REMOVE = [
    'translation_request',
    'partially_translated',
    'check_translation',
]
POST_PATTERN = re.compile(r'(\D+?)(\d+)')


class Note(object):
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

    def __str__(self):
        body = (self.body if len(self.body) < 30 else self.body[0:27] + '...')
        return "{width}x{height} {x},{y} {body}".format(
            width=self.width,
            height=self.height,
            x=self.x,
            y=self.y,
            body=body,
        )


@add_metaclass(ABCMeta)
class BooruPost(object):
    """
    A post on a booru-style imageboard.
    """
    def __init__(self, post_id):
        self.post_id = post_id
        self.post_url = self.post_url.format(post_id=post_id)

    def __str__(self):
        return '{0} Post - {1}'.format(self.site_name, self.post_id)

    @cached_property
    def auth(self):
        """
        Return the information necessary to use the site as a registered user.

        The credentials for a site can theoretically be many different forms, but they will
        typically be either a username and an API key or pickled cookies from a requests session
        that have the username and password hash.
        :return: authentication information
        :rtype: dict[str, str]
        """
        auth_filename = self.site_name.lower() + '.auth'

        if os.path.isfile(auth_filename):
            with open(auth_filename, 'rb') as auth_file:
                auth = pickle.load(auth_file)
            return auth
        else:
            store = yes_no('Store {0} login information?'.format(self.site_name))
            username = input('Username: ')
            auth_string = getpass.getpass(self.auth_prompt + ': ')

        if self.uses_cookies:
            session = self.login(username, auth_string)
            auth = requests.utils.dict_from_cookiejar(session.cookies)
        else:
            auth = {'login': username, 'api_key': auth_string}

        if store:
            with open(auth_filename, 'wb') as auth_file:
                pickle.dump(auth, auth_file)

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

    def scale_note(self, source_note, source_post):
        """
        Transforms a note to be proportional to the destination image.

        :return: a new note
        :rtype: Note
        """
        image_width, image_height = self.dimensions
        source_image_width, source_image_height = source_post.dimensions
        x_ratio = image_width / source_image_width
        y_ratio = image_height / source_image_height
        scaled_width = source_note.width * x_ratio
        scaled_height = source_note.height * y_ratio
        scaled_x = source_note.x * x_ratio
        scaled_y = source_note.y * y_ratio

        return Note(scaled_x, scaled_y, scaled_width, scaled_height, source_note.body)

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
        for note in source_post.notes:
            if not same_size:
                note = self.scale_note(note, source_post)

            self.write_note(note)
            time.sleep(self.cooldown)

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
        del self.__dict__['notes']


class DanbooruPost(BooruPost):
    site_name = 'Danbooru'
    short_code = 'd'
    domain = 'danbooru.donmai.us'
    base_url = 'https://' + domain
    post_url = base_url + '/posts/{post_id}.json'
    note_url = base_url + '/notes.json'
    auth_prompt = 'API key'
    uses_cookies = False
    cooldown = 1

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
        r = requests.get(self.post_url, params=self.auth)
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
        requests.put(self.post_url, data=payload, params=self.auth)


class GelbooruPost(BooruPost):
    site_name = 'Gelbooru'
    short_code = 'g'
    domain = 'gelbooru.com'
    base_url = 'https://' + domain
    login_url = base_url + '/index.php?page=account&s=login&code=00'
    # Not all API calls support JSON and those that do are often incomplete, so just use XML
    post_url = base_url + '/index.php?page=dapi&s=post&q=index&id={post_id}'
    note_url = base_url + '/index.php?page=dapi&s=note&q=index&post_id={post_id}'
    auth_prompt = 'Password'
    uses_cookies = True
    cooldown = 15  # Actual cooldown is 10 seconds, but give it a lot of wiggle room

    def login(self, username, password):
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
        r = requests.get(self.post_url, cookies=self.auth)
        root = ET.fromstring(r.text)
        d = convert_xml_to_dict(root)
        return d['posts'][0]

    @property
    def dimensions(self):
        return self.post_info['height'], self.post_info['width']

    @cached_property
    def notes(self):
        self.note_url = self.note_url.format(post_id=self.post_id)
        notes = []
        r = requests.get(self.note_url, cookies=self.auth)
        root = ET.fromstring(r.text)
        d = convert_xml_to_dict(root)
        api_notes = d['notes']

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
        requests.post(url, data=payload, cookies=self.auth)

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
            'pconf': pconf,
            'lupdated': lupdated,
            'submit': submit,
        }
        url = self.base_url + '/public/edit_post.php'
        requests.post(url, data=payload, cookies=self.auth)


def get_valid_classes():
    """
    :return: a list of classes representing the sites supported by this script
    :rtype: list[BooruPost]
    """
    classes = [cls[1] for cls in inspect.getmembers(sys.modules[__name__], inspect.isclass)]
    valid_classes = []

    for cls in classes:
        if issubclass(cls, BooruPost):
            try:
                # Ensure that only implemented classes get returned
                cls.domain
                valid_classes.append(cls)
            except AttributeError:
                continue

    return valid_classes


def copy_notes(valid_classes, source_id, destination_id):
    """
    Copy notes from the source post to the destrination post

    :param valid_classes: classes representing the supported sites
    :type valid_classes: list of BooruPost classes
    :param source_id: the site code and post number of the source post
    :type source_id: str
    :param destination_id: the site code and post number of the destination post
    :type destination_id: str
    """
    source = instantiate_post(valid_classes, source_id)
    destination = instantiate_post(valid_classes, destination_id)
    destination.copy_notes_from_post(source)


def instantiate_post(valid_classes, post_string):
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
    matches = re.search(POST_PATTERN, post_string)
    site_identifier, post_id = matches.groups()

    for cls in valid_classes:
        if site_identifier.lower() in (cls.short_code, cls.domain):
            return cls(post_id)

    # TODO: This should probably be a custom exception
    raise Exception('No supported site found for identifier: ' + site_identifier)


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
