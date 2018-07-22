import argparse
import sys
import time

from . import note_copy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', action='store', type=str,
                        help='The post from which notes will be copied')
    parser.add_argument('-d', '--destination', action='store', type=str,
                        help='The post to which notes will be copied')
    parser.add_argument('-f', '--file', action='store', type=str,
                        help='File containing post pairs, separated by whitespace, one per line')
    args = parser.parse_args()
    valid_classes = note_copy.get_valid_classes()

    if args.source and args.destination:
        note_copy.copy_notes(valid_classes, args.source, args.destination)
    elif args.file:
        cooldown = max(cls.cooldown for cls in valid_classes)
        with open(args.file, 'r') as f:
            for line in f:
                line = line.strip()

                # Ignore blank lines
                if not line:
                    continue

                source_id, destination_id = line.split()
                note_copy.copy_notes(valid_classes, source_id, destination_id)
                time.sleep(cooldown)
    elif args.source or args.destination:
        print('Specify two post numbers', file=sys.stderr)
        sys.exit(1)
    else:
        print('No post numbers or file specified', file=sys.stderr)
        sys.exit(1)
