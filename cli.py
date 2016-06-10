#!/usr/bin/python
import argparse
from utils.sc import SoundCloudService as sc

# TODO: Assume some JSON file for credentials

def main():
    parser = argparse.ArgumentParser(
        description='Utilities to work with SoundCloud and other services.'
    )

    subparsers = parser.add_subparsers(help='sub-command help')

    # --- All-in-one parser
    all_parser = subparsers.add_parser(
        'all', help='All-in-one: audio download to YouTube upload'
    )

    # TODO: Handle multiple files

    # ---- Download parser ----
    download_parser = subparsers.add_parser(
        'download', help='Download audio'
    )
    download_parser.add_argument(
        'url',
        help='URL where soundtrack track can be found'
    )
    download_parser.set_defaults(func=sc().download)

    # ---- Encode parser ----
    encode_parser = subparsers.add_parser(
        'video', help='Encode audio to video'
    )

    # ---- YouTube parser ----
    # TODO: Sync information between soundcloud and youtube?
    youtube_parser = subparsers.add_parser(
        'youtube', help='Upload video to YouTube'
    )

    # Process Arguments
    args, unknown = parser.parse_known_args()
    kwargs = vars(args)

    # Run whichever sub-command is necessary
    args.func(**kwargs)

if __name__ == "__main__":
    main()
