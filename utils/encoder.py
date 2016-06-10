from ffmpy import FFmpeg
import os

class VideoEncoder(object):
    def __init__(self):
        self.logo = './data/logo.png'

    def audio_to_video(self, filename, video_filename=None, **kwargs):
        if not video_filename:
            title = os.path.splitext(filename)[0]
            video_filename = '{}.mp4'.format(title)

        ff = FFmpeg(
            inputs={filename: None, self.logo: '-loop 1 -framerate 2'},
            outputs={video_filename: '-vf scale=854:480 -c:v libx264 -preset slow -tune stillimage -crf 18 -c:a copy -shortest -pix_fmt yuv420p'}
        )
        ff.run()
