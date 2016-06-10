import httplib
import httplib2
import os
import sys
import time
import json
from datetime import datetime

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

class YouTube(object):
    YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    CLIENT_SECRETS_FILE = "./data/youtube.json"

    MAX_RETRIES = 10
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
    RETRIABLE_EXCEPTIONS = (
        httplib2.HttpLib2Error,
        IOError,
        httplib.NotConnected,
        httplib.IncompleteRead,
        httplib.ImproperConnectionState,
        httplib.CannotSendRequest,
        httplib.CannotSendHeader,
        httplib.ResponseNotReady,
        httplib.BadStatusLine
    )

    PRIVATE = 'private'
    UNLISTED = 'unlisted'
    PUBLIC = 'public'
    VALID_PRIVACY_STATUSES = (PUBLIC, PRIVATE, UNLISTED)

    # These should be pulled from youtube as they are region specific...
    # ... but I don't have time for this!
    CATEGORIES = {
        'animation': 1,
        'gaming': 20,
        'vlog': 21,
        'people': 22,
        'comedy': 23,
        'entertainment': 24,
        'howto': 26
    }

    def __init__(self):
        self.delete_json = False

    def client(self):
        if self.__yt:
            return self.__yt

        flow = flow_from_clientsecrets(
            self.CLIENT_SECRETS_FILE,
            scope=self.YOUTUBE_READ_WRITE_SCOPE
        )

        storage = Storage("%s-oauth2.json" % sys.argv[0])
        credentials = storage.get()

        if credentials is None or credentials.invalid:
          credentials = run_flow(flow, storage)

        self.__yt = build(
            self.YOUTUBE_API_SERVICE_NAME,
            self.YOUTUBE_API_VERSION,
            http=credentials.authorize(httplib2.Http())
        )

        return self.__yt

    def upload(self, filename, **kwargs):
        self.__initialize_upload(filename, **kwargs)

    def __upload_details_from_file(self, filename):
        filename = '{}.json'.format(os.path.splitext(filename)[0])

        obj = {}
        with open(filename) as f:
            obj = json.loads(f.read())

        return obj.update({'filename': filename})

    def __initialize_upload(self, filename, **kwargs):
        try:
            obj = self.__upload_details_from_file(filename)
        except:
            obj = {}

        obj.update({k:v for k,v in kwargs.iteritems() if v})

        tags = kwargs.get('additional-tags')
        if tags:
            obj['tags'] += tags

        body = {
            'snippet': {
                'title': obj.get('title'),
                'description': obj.get('description'),
                'tags': obj.get('tags'),
                'categoryId': self.CATEGORIES.get('entertainment')

            },
            'status': {
                'privacyStatus': self.PRIVATE,
            }
        }

        print body

        # request = self.client().videos().insert(
        #     part=",".join(body.keys()),
        #     body=body,
        #     media_body=MediaFileUpload(
        #         filename,
        #         chunksize=-1,
        #         resumable=True
        #     )
        # )
        #
        # try:
        #     self.__resumable_upload(request)
        # except UploadException, e:
        #     raise e
        # else:
        #     filename = obj.get('filename')
        #     if filename and self.delete_json:
        #         os.remove(filename)

    def __resumable_upload(self, request):
        # TODO: Add more descriptive output

        response = None
        error = None
        retry = 0

        while response is None:
            try:
                print "Uploading file..."
                status, response = request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print "Video id '%s' was successfully uploaded." % response['id']
                    else:
                        raise UploadException("The upload failed with an unexpected response: %s" % response)
            except HttpError, e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
                else:
                    raise UploadException(e)
            except self.RETRIABLE_EXCEPTIONS, e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                print error
                retry += 1

                if retry > self.MAX_RETRIES:
                    raise UploadException("Exceeded max retries")

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print "Sleeping %f seconds and then retrying..." % sleep_seconds
                time.sleep(sleep_seconds)

class UploadException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
