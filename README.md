# note_copy - copy translations between booru-style imageboards


## Introduction
This script copies translation notes from one booru to another. Simply supply two post IDs:

    $ python note_copy.py --source danbooru.donmai.us1671559 --destination gelbooru.com2244172

The script can also read from a file to copy notes between multiple pairs at once. The file should have a pair of post IDs per line, with the IDs separated by whitespace.

    $ cat ids
    d1671559 g2244172
    d1701853 g2283415
    $ python note_copy.py --file ids

The lower-case prefixes are called short codes and - along with the domain name, as demonstrated above - can be used to identify the site on which the post is located.


## Requirements
- Python 3.4+
- [requests][requests]


## Usage
    usage: note_copy.py [-h] [-s SOURCE] [-d DESTINATION] [-f FILE]

    optional arguments:
      -h, --help            show this help message and exit
      -s SOURCE, --source SOURCE
                            The post from which notes will be copied
      -d DESTINATION, --destination DESTINATION
                            The post to which notes will be copied
      -f FILE, --file FILE  File containing post pairs, separated by whitespace,
                            one per line

You need to provide either a source and a destination post or a file; you cannot use both sets of arguments simultaneously.


## Supported sites
| Site Name       | Short Code   | Domain               |
|-----------------|--------------|----------------------|
| Danbooru        | `d`          | `danbooru.donmai.us` |
| Gelbooru        | `g`          | `gelbooru.com`       |



  [requests]: http://docs.python-requests.org/en/master/
