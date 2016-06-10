from time import strptime, mktime
from datetime import datetime
from tqdm import tqdm
import soundcloud
import requests
import shlex
import json
from urllib import urlencode
from datetimeencoder import DateTimeEncoder

MEGABYTE = 1024*1024

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

    def track_by_url(self, url):
        track = self.client().get('/resolve', url=url)
        return Track(track)

    def tracks(self, since=None, format='list', least_recent=True):
        params = {
            'created_at[from]': since
        }

        query = urlencode({k: v for k, v in params.iteritems() if v})
        if query:
            query = '?' + query

        tracks = self.client().get('/users/{}/tracks{}'.format(
            self.__settings.get('user'),
            query
        ), limit=self.LIMIT)

        if format == 'dict':
            return {track.title: Track(track) for track in tracks}

        track_list = map(Track, tracks)

        if least_recent:
            track_list.sort(key=lambda x: x.created_at)

        return track_list

    def download(self, url=None, since=None, **kwargs):
        if url:
            tracks = [self.track_by_url(url)]
        else:
            tracks = self.tracks(since=since)

        map(self.__download_track, tracks)

    def __download_track(self, track):
        # TODO: Don't download if exists
        title = track.title.replace("/","-")
        url = "{}?client_id={}".format(track.download, self.__settings.get('application'))
        filename = u"./data/{}.m4a".format(title)
        response = requests.get(url, stream=True)

        print('Downloading {}...'.format(filename))
        with open(filename, 'wb') as handle:
            for data in tqdm(response.iter_content(chunk_size=10 * MEGABYTE)):
                handle.write(data)

        track.save_to_json()

    def settings_from_json(self, filename=None):
        if not filename:
            filename = self.SOUNDCLOUD_SETTINGS_JSON

        with open(filename) as f:
            self.__settings = json.loads(f.read())

# Wouldn't need this normally, but we want to normalize certain fields
class Track(object):
    TIME_FORMAT = '%Y/%m/%d %H:%M:%S +0000'
    DEFAULT_TAGS = ['podcast']
    SAVE_FOLDER = './data/'

    def __init__(self, track):
        self.title = track.title
        self.url = track.permalink_url
        self.download = track.download_url
        self.slug = track.permalink
        self.description = track.description
        self.tags = Track.to_tag_list(track.tag_list)
        self.created_at = datetime.fromtimestamp(
            mktime(strptime(track.created_at, self.TIME_FORMAT))
        )

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def save_to_json(self, filename=None):
        if not filename:
            filename = '{}{}.json'.format(self.SAVE_FOLDER, self.title.replace("/","-"))

        with open(filename, 'w') as out:
            json.dump(self.__dict__, out, cls=DateTimeEncoder)

    @staticmethod
    def to_tag_list(input_string):
        tags = shlex.split(input_string)
        tags = [x.lower() for x in tags]
        tags = set(tags) | set(Track.DEFAULT_TAGS)
        return list(tags)
