from time import strptime, mktime
from datetime import datetime
import soundcloud
import shlex
import json

class SoundCloudService(object):
    SOUNDCLOUD_SETTINGS_JSON='./data/soundcloud.json'
    LIMIT=1000  # Pagination is not well documented; just grab them all for now

    def __init__(self):
        # TODO: Pass in credentials
        self.__client = None
        self.settings_from_json()
        self.client()

    def client(self):
        if not self.__client:
            self.__client = soundcloud.Client(client_id=self.__settings.get('application'))

        return self.__client

    def track(self, url):
        track = self.client().get('/resolve', url=url)
        return Track(track)

    def tracks(self, format='list'):
        tracks = self.client().get('/users/{0}/tracks'.format(
            self.__settings.get('user')
        ), limit=1)

        if format == 'dict':
            return {track.title: Track(track) for track in tracks}

        return map(SoundCloud.track_to_dict, tracks)

    def download(url):
        return self.track(url)

    def settings_from_json(self, filename=None):
        if not filename:
            filename = self.SOUNDCLOUD_SETTINGS_JSON

        with open(filename) as f:
            self.__settings = json.loads(f.read())

# Wouldn't need this normally, but we want to normalize certain fields
class Track(object):
    TIME_FORMAT = '%Y/%m/%d %H:%M:%S +0000'
    DEFAULT_TAGS = ['podcast']

    def __init__(self, track):
        self.title = track.title
        self.url = track.permalink_url,
        self.slug = track.permalink,
        self.description = track.description,
        self.tags = to_tag_list(track.tag_list),
        self.created_at = datetime.fromtimestamp(
            mktime(strptime(track.created_at, self.TIME_FORMAT))
        )

    @staticmethod
    def to_tag_list():
        tags = shlex.split(input_string)
        tags = [x.lower() for x in tags]
        tags = set(tags) | set(Track.DEFAULT_TAGS)
        return list(tags)
