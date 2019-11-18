# note_copy
## Copy translation notes between booru-style imageboards


[![Build Status](https://api.travis-ci.com/torsten-ostgard/booru-note-copy.svg?branch=master)](https://travis-ci.com/torsten-ostgard/booru-note-copy)
[![Codecov](https://codecov.io/gh/torsten-ostgard/booru-note-copy/branch/master/graph/badge.svg)](https://codecov.io/gh/torsten-ostgard/booru-note-copy)


## Introduction
`note_copy` is a program that copies translation notes from one booru post to another, either on the same site or across sites.


## Installation
The recommended way to install the `booru-note-copy` module is to simply use [`pipenv`](https://pipenv.org/):
```
$ pipenv install booru-note-copy
```
Or, if you prefer plain, old `pip`:
```
$ pip install --user booru-note-copy
```
Once installed, the program is accessible as `note_copy`.


## Example
To copy notes between posts, simply supply two post IDs:
```
$ note_copy --source d1671559 --destination g2244172
```
This will copy the notes from the source and change the tags on the destination post as necessary. On first usage, you will be prompted for your login information for each site used so that the notes can be created with your account. If you choose to store this data, the files are created in the `.note_copy` directory inside your home directory. For sites that require passwords, only the hash of the password is stored.

The script can also read from a file to copy notes between multiple pairs at once. The file should have a pair of post IDs per line, with the IDs separated by whitespace.
```
$ cat ids
d1671559 g2244172
d1701853 g2283415
$ note_copy --file ids
```
The lower-case prefixes are called short codes and can be used to identify the site on which the post is located. Alternatively, the full domain of the site can be used instead of the short code, e.g. `gelbooru.com2244172`.

`note_copy` is also able to be run as a module:
```
$ python -m note_copy -s d1102540 -d g1433185
```


## Requirements
- Python 3.5+


## Usage
```
usage: note_copy [-h] [-s SOURCE] [-d DESTINATION] [-f FILE]

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The post from which notes will be copied
  -d DESTINATION, --destination DESTINATION
                        The post to which notes will be copied
  -f FILE, --file FILE  File containing post pairs, separated by whitespace,
                        one per line
```
You need to provide either a source/destination combo or a file; you cannot use both sets of arguments simultaneously.


## Supported sites
| Site Name       | Short Code   | Domain               | Login Information           |
|-----------------|--------------|----------------------| --------------------------- |
| Danbooru        | `d`          | `danbooru.donmai.us` | Username, API key           |
| Gelbooru        | `g`          | `gelbooru.com`       | Username, password, API key |

