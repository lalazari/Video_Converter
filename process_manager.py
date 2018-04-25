import logging
import os
import subprocess

from dispatcher import Dispatcher
from utils import mkdir_p

logger = logging.getLogger('web')

IMAGE_TRANSCODE = "{0}{1}_image_transcoded_"
IMAGE_CROPPED = "{0}{1}_Cropped_images_{2}"
IMAGE_RESIZED = "{0}{1}_Resized_images_{2}"

AUDIO_TRANSCODE = "{0}{1}_audio_trancoded_"
AUDIO_CLIP = "{0}{1}_clip_audio_From_To_{2}"

CROP_PATH_OUT = '{0}{1}_CROPPED_{2}'
FRAME_PATH_OUT = '{0}{1}_Frames'
TRANSCODE_PATH_OUT = '{0}{1}_transcoded{2}'
AUDIO_FROM_VIDEO_PATH_OUT = '{0}{1}_Audio'


class ProcessManager(object):
    def __init__(self, credentials, file_manager):
        self.dispatcher = Dispatcher(credentials=credentials)
        self.file_manager = file_manager

    def image_processing(self, data, dir_v_path_out):
        need_check = False
        for img_path in self.file_manager.all_images:
            base_name = os.path.splitext(img_path)[0]
            logger.info("Base name Image " + str(base_name))

            ext = os.path.splitext(img_path)[1]
            if need_check:
                data["image_out_format"] = ext

            if not data.get('image_out_format'):
                data["image_out_format"] = ext
                need_check = True
            if data["image_out_format"] not in ext:
                path_transcode = IMAGE_TRANSCODE.format(dir_v_path_out, base_name)
                mkdir_p(path_transcode)
                self.dispatcher.image_transcode(img_path, path_transcode, data["image_out_format"])

            logger.info("FORMAT IMAGE " + str(data["image_out_format"]))

            if data.get("crop_image"):
                path_cropped = IMAGE_CROPPED.format(dir_v_path_out, base_name,
                                                    data["crop_image"].replace(":", "-"))
                logger.info(path_cropped)
                mkdir_p(path_cropped)

                self.dispatcher.image_crop(img_path, path_cropped, base_name, data)

            if data.get('resize_image'):
                path_resized = IMAGE_RESIZED.format(dir_v_path_out, base_name,
                                                    data["resize_image"].replace("x", "-"))
                mkdir_p(path_resized)

                self.dispatcher.image_resize(img_path, path_resized,
                                             base_name, data)

    def audio_processing(self, data, dir_v_path_out):

        for au_path in self.file_manager.all_audio:
            base_name = os.path.splitext(au_path)[0]
            logger.info("Base name Audio " + str(base_name))

            ext = os.path.splitext(au_path)[1]

            if not data.get('audio_out_format'):
                data["audio_out_format"] = ext

            if data["audio_out_format"] not in ext:
                path_transcode = AUDIO_TRANSCODE.format(dir_v_path_out, base_name)
                mkdir_p(path_transcode)
                self.dispatcher.audio_transcode(au_path, path_transcode, base_name, data["audio_out_format"])

            if ("audio_out_format" not in data) or (
                        data["audio_out_format"] in ""):
                data["audio_out_format"] = os.path.splitext(au_path)[1]

            logger.info("AUDIO FORMAT " + str(data["audio_out_format"]))
       
            if data.get("clip_audio"):
                path_clipped = AUDIO_CLIP.format(dir_v_path_out, base_name,
                                                    data["clip_audio"].replace("to", "-"))
                logger.info(path_clipped)
                mkdir_p(path_clipped)

                self.dispatcher.audio_clip(au_path, path_clipped, base_name, data)

    def video_processing(self, data, dir_v_path_in, dir_v_path_out, dbconn=None):
        for v_path in self.file_manager.all_videos:

            base_name = os.path.splitext(v_path)[0]
            logger.info("Base NAME " + str(base_name))

            if "v_out_format" not in data:
                video_format = os.path.splitext(v_path)[1]
                data["v_out_format"] = video_format

            if "rotate_video" in data:
                # Rotate Video
                rotate_path_out = base_name + '_ROTATED_' + data[
                    "rotate_video"] + data["v_out_format"]
                logger.info("Rotate Path " + str(rotate_path_out))

            v_clip_video = ""
            if "clip_video" in data:
                # Video Clip / Cut part of Video
                v_clip_video = data["clip_video"]
                data_clip_video = data["clip_video"].replace(":", "-")
                clip_path_out = base_name + "_Cut_From_To" + data_clip_video
                logger.info("Clip Path " + str(clip_path_out))

            # Video Convertion
            v_path_out = base_name + '_transcoded' + data["v_out_format"]
            logger.info("V_PATH OUT  " + str(v_path_out))
            # Create Frames, unique output name for each frame
            frame_path_out = base_name + '%03d' + '.bmp'  # for the frames
            # Crop Video
            crop_path_out = base_name + '_CROPPED_'  # + data[
            # "v_out_format"]

            # Audio Convertion
            a_path_out_wav = base_name + '.wav'

            v_crop = data.get("crop_video", '')
            v_extract_frames = data.get("extract_frames", '')
            v_transcode = data.get("transcode_video", False)
            v_rotate = data.get("rotate_video", '')
            v_extract_audio = data.get("extract_audio", False)

            # Delay method is needed if we want to process the task
            # asynchronously.
            if v_crop:
                crop_path = CROP_PATH_OUT.format(dir_v_path_out, base_name, v_crop)
                #mkdir_p(crop_path)

                self.dispatcher.convert_video_crop(v_path, v_crop,
                                                   dir_v_path_out,
                                                   crop_path,
                                                   data)

                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"],
                                 "Action": "Video_crop",
                                 "Parameters": data["crop_video"],
                                 "Input_Video": base_name})
            if v_extract_frames:
                frames_path =  FRAME_PATH_OUT.format(dir_v_path_out, base_name)
                mkdir_p(frames_path)

                self.dispatcher.convert_video_frames(v_path,
                                                     dir_v_path_out,
                                                     frames_path,
                                                     base_name, data)

                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"],
                                 "Action": "Frame_Extraction",
                                 "Parameters": data["extract_frames"],
                                 "Input_Video": base_name})
            if v_transcode:

                transcode_path =  TRANSCODE_PATH_OUT.format(dir_v_path_out, base_name, data[
                                                            "v_out_format"])
                mkdir_p(transcode_path)
                # subprocess.call(
                #     ['mkdir', dir_v_path_out + base_name + "_transcoded"])
                self.dispatcher.convert_video_transcode(v_path,
                                                        dir_v_path_out,
                                                        transcode_path,
                                                        base_name,
                                                        data["v_out_format"])

                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"],
                                 "Action": "Transcode_video",
                                 "Parameters": data["v_out_format"],
                                 "Input_Video": base_name})
            if v_rotate:
                subprocess.call(
                    ['mkdir', dir_v_path_out + base_name +
                     '_ROTATED_' +
                     data["rotate_video"]])
                self.dispatcher.convert_video_rotate(v_path, v_rotate, dir_v_path_out,
                                                     base_name, data)

                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"],
                                 "Action": "Rotate_Video",
                                 "Parameters": data["rotate_video"],
                                 "Input_Video": base_name})

            if v_extract_audio:
                extract_audio_path = AUDIO_FROM_VIDEO_PATH_OUT.format(dir_v_path_out, base_name)
                mkdir_p(extract_audio_path)

                self.dispatcher.convert_video_audio(v_path,
                                                    dir_v_path_out,
                                                    base_name,
                                                    extract_audio_path,
                                                    a_path_out_wav)
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"],
                                 "Action": "Audio_Extraction",
                                 "Parameters": data["extract_audio"],
                                 "Input_Video": base_name})

            if v_clip_video:
                logger.info("CREATE DIR " + str(dir_v_path_out) + "    " + str(
                    clip_path_out))
                #subprocess.call(['mkdir', dir_v_path_out + clip_path_out])

                self.dispatcher.convert_video_clip(v_path,
                                                   dir_v_path_out,
                                                   clip_path_out, data)
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"],
                                 "Action": "Clip_Video",
                                 "Parameters": data["clip_video"],
                                 "Input_Video": base_name})

            if ("rescale_video" in data) and (data["rescale_video"] not in ""):
                logger.info("Rescale Parameters " + str(data["rescale_video"]))
                if not os.path.isdir(dir_v_path_out + base_name + "rescale_To_" + data[
                    "rescale_video"]):
                    subprocess.call(['mkdir',
                                     dir_v_path_out + base_name +
                                     "rescale_To_" +
                                     data["rescale_video"]])
                    self.dispatcher.video_rescale(v_path, dir_v_path_out, base_name,
                                                  data)