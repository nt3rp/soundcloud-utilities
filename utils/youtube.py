import httplib
import httplib2
import os
import sys
import time
import json
from argparse import Namespace
from datetime import datetime
from glob import glob

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
    SRC_FOLDER = './data/'
    CLIENT_SECRETS_FILE = "{}youtube.json".format(SRC_FOLDER)

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

    # Hack: Otherwise, will use arguments passed to main application
    RUN_FLOW_ARGS = Namespace(
        logging_level='ERROR',
        auth_host_name='localhost',
        noauth_local_webserver=False,
        auth_host_port=[8080, 8090]
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
        self.__client = None
        self.delete_files = True

    def client(self):
        if self.__client:
            return self.__client

        flow = flow_from_clientsecrets(
            self.CLIENT_SECRETS_FILE,
            scope=self.YOUTUBE_READ_WRITE_SCOPE,
        )

        storage = Storage("%s-oauth2.json" % sys.argv[0])
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, flags=self.RUN_FLOW_ARGS)

        self.__client = build(
            self.YOUTUBE_API_SERVICE_NAME,
            self.YOUTUBE_API_VERSION,
            http=credentials.authorize(httplib2.Http())
        )

        return self.__client

    def auth(self, **kwargs):
        # hack
        del kwargs['func']
        self.client()

    def upload(self, filename=None, **kwargs):
        # hack
        del kwargs['func']

        if filename:
            files = [filename]
        else:
            files = sorted(glob('{}*.mp4'.format(self.SRC_FOLDER)), key=os.path.getmtime)

        map(lambda x: self.__initialize_upload(x, **kwargs), files)

    def __upload_details_from_file(self, filename):
        filename = '{}.json'.format(os.path.splitext(filename)[0])

        obj = {}
        with open(filename) as f:
            obj = json.loads(f.read())

        obj.update({'filename': filename})
        return obj

    def __initialize_upload(self, filename, **kwargs):
        try:
            obj = self.__upload_details_from_file(filename)
        except:
            obj = {}

        obj.update({k:v for k,v in kwargs.iteritems() if v})

        tags = kwargs.get('additional-tags')
        if tags:
            obj['tags'] += tags

        privacy = self.PRIVATE
        if kwargs.get('public'):
            privacy = self.PUBLIC

        body = {
            'snippet': {
                'title': obj.get('title'),
                'description': obj.get('description'),
                'tags': obj.get('tags'),
                'categoryId': self.CATEGORIES.get('entertainment')

            },
            'status': {
                'privacyStatus': privacy
            }
        }

        request = self.client().videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(
                filename,
                chunksize=-1,
                resumable=True
            )
        )

        try:
            self.__resumable_upload(request)
        except UploadException, e:
            raise e
        else:
            if not self.delete_files:
                return

            os.remove(filename)

            data_filename = obj.get('filename')
            if data_filename:
                os.remove(data_filename)

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
