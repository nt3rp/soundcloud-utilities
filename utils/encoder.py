from ffmpy import FFmpeg
from glob import glob
import os

class VideoEncoder(object):
    SRC_FOLDER = './data/'

    def __init__(self):
        self.logo = '{}logo.png'.format(self.SRC_FOLDER)
        self.delete_audio = True

    def audio_to_video(self, filename=None, **kwargs):
        if filename:
            files = [filename]
        else:
            files = sorted(glob('{}*.m4a'.format(self.SRC_FOLDER)), key=os.path.getmtime)

        map(self.__audio_to_video, files)

    def __audio_to_video(self, filename=None, **kwargs):
        # TODO: Don't encode if already exists
        title = os.path.splitext(filename)[0]
        video_filename = '{}.mp4'.format(title)

        ff = FFmpeg(
            inputs={filename: None, self.logo: '-loop 1 -framerate 2'},
            outputs={video_filename: '-vf scale=854:480 -c:v libx264 -preset slow -tune stillimage -crf 18 -c:a copy -shortest -pix_fmt yuv420p'}
        )

        print ff.cmd
        ff.run()

        if self.delete_audio:
            os.remove(filename)
