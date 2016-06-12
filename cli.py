#!/usr/bin/python
import argparse
from datetime import datetime
from utils.sc import SoundCloudService as sc
from utils.encoder import VideoEncoder as v
from utils.youtube import YouTube as yt

# TODO: Assume some JSON file for credentials

def main():
    # TODO: Make 'filename' optional for encoder, youtube: default to 'all'
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
    # TODO: Since date: download all audio after a certain date
    download_parser = subparsers.add_parser(
        'download', help='Download audio'
    )
    download_parser.add_argument(
        '--url',
        help='URL where soundtrack track can be found'
    )
    download_parser.add_argument(
        '--since',
        help='URL where soundtrack track can be found',
        type=valid_date
    )
    download_parser.set_defaults(func=sc().download)

    # ---- Encode parser ----
    encode_parser = subparsers.add_parser(
        'video', help='Encode audio to video'
    )
    encode_parser.add_argument(
        '--filename',
        help='Audio file to convert to video'
    )
    encode_parser.set_defaults(func=v().audio_to_video)

    # ---- YouTube parser ----
    # TODO: Sync information between soundcloud and youtube?
    youtube_parser = subparsers.add_parser(
        'youtube', help='Upload video to YouTube'
    )
    youtube_parser.add_argument(
        '--filename',
        help='Video file to upload'
    )
    youtube_parser.add_argument(
        '--description',
        help='Description for video'
    )
    youtube_parser.add_argument(
        '--title',
        help='Title for video'
    )
    youtube_parser.add_argument(
        '--tags',
        nargs='*',
        help='Tags for video'
    )
    youtube_parser.add_argument(
        '--additional-tags',
        nargs='*',
        help='Additional tags for video'
    )
    youtube_parser.add_argument(
        '--public',
        dest='public',
        action='store_true',
        help='Additional tags for video'
    )
    youtube_parser.set_defaults(
        func=yt().upload,
        public=False
    )

    youtube_auth_parser = subparsers.add_parser(
        'auth', help='Authorize YouTube'
    )
    youtube_auth_parser.set_defaults(func=yt().auth)

    # Process Arguments
    args, unknown = parser.parse_known_args()
    kwargs = vars(args)

    # Run whichever sub-command is necessary
    args.func(**kwargs)

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

if __name__ == "__main__":
    main()
