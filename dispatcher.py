from celery_tasks import (convert_video_crop, audio_transcode, audio_clip,
                          image_transcode, image_crop, image_resize, convert_video_rotate,
                          convert_video_audio, convert_video_clip, video_rescale, process_all_tasks,
                          convert_video_transcode, convert_video_frames)
import logging
import copy
from copy import deepcopy

#logger = logging.getLogger('web')
class Dispatcher(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.tasks = []

    def dispatch(self, data):
        process_all_tasks(self.tasks, self.credentials, data)

    def image_transcode(self, img_path, path, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(image_transcode.s(img_path, path, cp_data))

    def image_crop(self, img_path, path, base_name, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(image_crop.s(img_path, path, base_name, cp_data))

    def image_resize(self, img_path, dir_v_path_out,
                     base_name, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(image_resize.s(img_path, dir_v_path_out, base_name, cp_data))

    def audio_transcode(self, au_path, dir_v_path_out, base_name, audio_out_format):
        self.tasks.append(audio_transcode.s(au_path, dir_v_path_out, base_name,
                                            audio_out_format))

    def audio_clip(self, au_path, dir_v_path_out, base_name, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(audio_clip.s(au_path, dir_v_path_out, base_name, cp_data))

    def convert_video_transcode(self, v_path, dir_v_path_out, transcode_path, base_name, v_out_format):
        self.tasks.append(
            convert_video_transcode.s(v_path, dir_v_path_out, transcode_path, base_name, v_out_format))

    def convert_video_crop(self, v_path, v_crop, dir_v_path_out, crop_path_out, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(convert_video_crop.s(v_path, v_crop, dir_v_path_out, crop_path_out, cp_data))

    def convert_video_frames(self, v_path, dir_v_path_out, frame_path_out,
                             base_name, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(convert_video_frames.s(v_path,
                                                 dir_v_path_out,
                                                 frame_path_out,
                                                 base_name, cp_data))

    def convert_video_rotate(self, v_path, v_rotate, dir_v_path_out,
                             base_name, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(convert_video_rotate.s(v_path, v_rotate, dir_v_path_out,
                                                 base_name, cp_data))

    def convert_video_audio(self, v_path,
                            dir_v_path_out,
                            base_name,
                            extract_audio_path,
                            a_path_out_wav):
        self.tasks.append(convert_video_audio.s(v_path,
                                                dir_v_path_out,
                                                base_name,
                                                extract_audio_path,
                                                a_path_out_wav))

    def convert_video_clip(self, v_path, dir_v_path_out, clip_path_out, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(convert_video_clip.s(v_path,
                                               dir_v_path_out,
                                               clip_path_out,cp_data))

    def video_rescale(self, v_path, dir_v_path_out, base_name, data):
        cp_data = copy.deepcopy(data)
        self.tasks.append(video_rescale.s(v_path, dir_v_path_out, base_name, cp_data))
