import os
import glob

import delegator
from celery.utils.log import get_task_logger

from utils import mkdir_p

logger = get_task_logger('celery_logs')


class VideoCommands(object):

    def convert_video_crop(self, v_path, crop, output_path, crop_output_path, data):

        command_string = 'ffmpeg -i {path} -filter:v crop={crop} -c:a copy {output}'

        file_name = os.path.basename(crop_output_path) + data['temp']
        mkdir_p(crop_output_path)
        final_path = os.path.join(output_path, crop_output_path, file_name)

        command = command_string.format(path=v_path,
                                        crop=crop,
                                        output=final_path,
                                        format=data['temp'])
        self._run(command)
        return final_path

    def convert_video_frames(self, v_path, dir_v_path_out, frames_path, base_name,
                             extract_frames):
        command_string = 'ffmpeg -i {path} -r {fps} {output}'

        fps = self._get_fps_from_probe(v_path)
        fps = fps.strip()
        fps = float(fps.split('/')[0]) / float(fps.split('/')[1])

        i_fps = 1000 / float(extract_frames) if extract_frames != 0 else 1000 / float(fps) 
        final_fps = i_fps if float(i_fps) <= float(fps) else fps

        final_path = self._get_final_path(base_name, dir_v_path_out, file_postfix='_f%04d' + '.bmp',
                                  folder_postfix='')

        command = command_string.format(path=v_path,
                                        fps=final_fps,
                                        output=final_path)

        logger.info(command)
        self._run(command)

        pathh = base_name + dir_v_path_out
        pathh = pathh.split(base_name)[1]

        self.rename(pathh + base_name, '*_f[0-9]*.bmp', 1.0/float(final_fps))
        return final_path

    def convert_video_transcode(self, v_path, dir_v_path_out, transcode_path, base_name, v_out_format):
        # -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        # in order to not have not scalling issues "height not divisible by
        # 2", because .h264 need even dimensions
        # Divide the original height and width by 2, Round it down to the
        # nearest pixel, Multiply it by 2 again, thus making it an even number
        # https://stackoverflow.com/questions/20847674/ffmpeg-libx264-height
        # -not-divisible-by-2 and
        # compress https://superuser.com/questions/1041075/what-is-the-best
        # -way-to-losslessly-compress-mjpeg-to-mp4

        out = self._get_codec_from_probe(v_path).strip()

        final_path = self._get_final_path(base_name, dir_v_path_out,
                                          folder_postfix='_transcoded' + v_out_format,
                                          file_postfix=v_out_format)
        if out == "mjpeg":
            command_string = ('ffmpeg -i {path} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -preset veryslow -crf 18 {output}')
            command = command_string.format(path=v_path,
                                            output=final_path)
            self._run(command)
            return final_path

        command_string = 'ffmpeg -y -i {path} -c:v libx264 -crf 23 -c:a aac -q:a 100 {output}'
        command = command_string.format(path=v_path,
                                    output=final_path)
        self._run(command)
        return final_path

    def convert_video_rotate(self, v_path, v_rotate, dir_v_path_out, base_name, data):
        final_path = self._get_final_path(base_name, dir_v_path_out,
                                          folder_postfix='_ROTATED_' + data['rotate_video'],
                                          file_postfix='_ROTATED_' + data['temp'])
        command_string = 'ffmpeg -i {path} -vf transpose={rotation} {output}'
        command = command_string.format(path=v_path,
                                        rotation=v_rotate,
                                        output=final_path)
        self._run(command)
        return final_path

    def convert_video_audio(self, v_path, dir_v_path_out, base_name, extract_audio_path, a_path_out_wav):

        final_path = self._get_final_path(base_name, dir_v_path_out, 
                                        folder_postfix='_Audio', 
                                        file_postfix='_Audio.mp3')

        command_string = 'ffmpeg -y -i {path} {output}'
        command = command_string.format(path=v_path,
                                        output=final_path)
        self._run(command)
        return final_path

    def convert_video_clip(self, v_path, dir_v_path_out, clip_path_out, data):

        from_clip = data["clip_video"].split('to')[0]
        to_clip = data["clip_video"].split('to')[1]
        file_name = os.path.basename(clip_path_out) + data['temp']
        final_path = os.path.join(dir_v_path_out + clip_path_out)
        mkdir_p(final_path)

        command_string = ('ffmpeg -i {path} -vcodec copy -acodec '
                          'copy -ss {from_clip} -to {to_clip} {output}')
        command = command_string.format(path=v_path,
                                        from_clip=from_clip,
                                        to_clip=to_clip,
                                        output=final_path+ '/' +  os.path.basename(clip_path_out) + data['temp'])
        self._run(command)
        return final_path

    def video_rescale(self, v_path, dir_v_path_out, base_name, data):

        rescale_video = data['rescale_video']
        file_format = data['temp']
        final_path = self._get_final_path(base_name, dir_v_path_out,
                                          folder_postfix="rescale_To_{}".format(rescale_video),
                                          file_postfix="rescale_To_{}".format(file_format))
        command_string = 'ffmpeg -i {path} -vf scale={rescale_video} {output}'
        command = command_string.format(path=v_path,
                                        rescale_video=rescale_video,
                                        output=final_path)
        self._run(command)
        return final_path

    @staticmethod
    def _get_final_path(base_name, dir_v_path_out, folder_postfix=None, file_postfix=None):
        folder_name = base_name + folder_postfix
        logger.info(folder_name)

        folder_path = dir_v_path_out + folder_name

        mkdir_p(folder_path)
        file_name = os.path.basename(base_name) + file_postfix
        final_path = os.path.join(folder_path, file_name)
        logger.info( final_path)
        return final_path

    @staticmethod
    def _run(command):
        result = delegator.run(command, timeout=3600)
        logger.info("Executing command: [ {} ]".format(command))
        if result.return_code != 0:
            logger.error(result.err)
            raise VideoException(msg=result.err)
        logger.info("result: {}".format(result.out))
        return result.out

    def _get_fps_from_probe(self, path):
        command_string = ('ffprobe -v 0 -of csv=p=0 -select_streams '
                          '0 -show_entries stream=r_frame_rate {}'.format(path))
        return self._run(command_string)

    def _get_codec_from_probe(self, path):
        command_string = (
            'ffprobe -v error -select_streams v:0 '
            '-show_entries stream=codec_name '
            '-of default=noprint_wrappers=1:nokey=1 {}'.format(path))

        return self._run(command_string)

    @staticmethod
    def rename(dire, pattern, fps):
        for pathAndFilename in glob.iglob(os.path.join(dire, pattern)):
            bname, ext = os.path.splitext(os.path.basename(pathAndFilename))
            bidx = bname.rindex("_f") + 2
            frame_s = bname[bidx:]
            frame = int(frame_s)
            ms = int(frame * fps * 1000)
            new_name = bname + "_ms" + str(ms) + ext
            os.rename(pathAndFilename, os.path.join(dire, new_name))


def get_video_commands_manager():
    return VideoCommands()


class VideoException(Exception):
    def __init__(self, msg):
        self.msg = msg
