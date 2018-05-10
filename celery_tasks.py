import json
import os
import subprocess

import stomp
import time
from PIL import Image
from celery import Celery, group
from celery.result import allow_join_result
from celery.utils.log import get_task_logger

from video_commands import get_video_commands_manager, VideoException

broker = "amqp://admin:mypass@broker:5672//"
# CELERY_RESULT_BACKEND ='amqp://admin:mypass@broker:5672//'
# broker_api = "amqp://admin:mypass@broker:15672/api/"
celery = Celery("tasks", backend=broker, broker=broker)  # ,
# worker_send_task_events = True, event_queue_expires = 240)

# Celery Tasks
"""Video Tasks"""

video_manager = get_video_commands_manager()
logger = get_task_logger('celery_logs')


# Cropping Video Task
@celery.task
def convert_video_crop(v_path, v_crop, dir_v_path_out, crop_path_out, data):
    try:
        final_path = video_manager.convert_video_crop(v_path,
                                                      v_crop,
                                                      dir_v_path_out,
                                                      crop_path_out,
                                                      data)
        final_path = os.path.basename(final_path)
        return {"status": "COMPLETED",
                "final_path": final_path}
    except VideoException as exc:
        return {"status": "FAILED {0} to crop video with parameters {1}".format(
                os.path.basename(v_path), v_crop)}
    except Exception as exc:
        return {"status": "FAILED {0} to crop video with parameters {1}".format(
                os.path.basename(v_path), v_crop)}

# Convert video to frames
@celery.task
def convert_video_frames(v_path, dir_v_path_out, frame_path_out, base_name,
                         data):
    try:
        final_path = video_manager.convert_video_frames(v_path,
                                                        dir_v_path_out,
                                                        frame_path_out,
                                                        base_name,
                                                        float(data[
                                                        "extract_frames"]))
        final_path = os.path.basename(final_path)
        return {"status": "COMPLETED",
                "final_path": final_path.split("_")[0] + '_Frame_Extraction'}
    except VideoException as exc:
        return {"status": "FAILED {0} to extract frames".format(
            os.path.basename(v_path))}
    except Exception as exc:
        return {"status": "FAILED {0} to extract frames".format(
            os.path.basename(v_path))}


# Transcode Video
@celery.task
def convert_video_transcode(v_path, dir_v_path_out, transcode_path, base_name,
                             v_out_format):
    # Check the codec
    try:
        final_path = video_manager.convert_video_transcode(v_path,
                                                           dir_v_path_out,
                                                           transcode_path,
                                                           base_name,
                                                           v_out_format)
        final_path = os.path.basename(final_path)
        return {"status": "COMPLETED",
                "final_path": final_path}
    except VideoException as exc:
        return {"status": "FAILED {}".format(exc)}
    except Exception as exc:
        return {"status": "FAILED {}".format(exc)}



# Rotate Video
@celery.task
def convert_video_rotate(v_path, v_rotate, dir_v_path_out, base_name, data):
    try:
        final_path = video_manager.convert_video_rotate(v_path,
                                                        v_rotate,
                                                        dir_v_path_out,
                                                        base_name,
                                                        data)
        final_path = os.path.basename(final_path)
        return {"status": "COMPLETED",
                "final_path": final_path}
    except VideoException as exc:
        return {"status": "FAILED {0} to rotate video with parameter {1}".format(
            os.path.basename(v_path), v_rotate)}
    except Exception as exc:
        return {"status": "FAILED {0} to rotate video with parameter {1}".format(
            os.path.basename(v_path), v_rotate)}


# Extract Audio
@celery.task
def convert_video_audio( v_path, dir_v_path_out, base_name, extract_audio_path,
                         a_path_out_wav):

    try:
        final_path = video_manager.convert_video_audio(v_path,
                                                       dir_v_path_out,
                                                       base_name,
                                                       extract_audio_path,
                                                       a_path_out_wav)
        final_path = os.path.basename(final_path)
        return {"status": "COMPLETED",
                "final_path": final_path}
    except VideoException as exc:
        return {"status": "FAILED {0} to extract audio".format(
            os.path.basename(v_path))}
    except Exception as exc:
        return {"status": "FAILED {0} to extract audio".format(
            os.path.basename(v_path))}

# Clip Video
@celery.task
def convert_video_clip(v_path, dir_v_path_out, clip_path_out, data):
    try:
        final_path = video_manager.convert_video_clip(v_path,
                                                      dir_v_path_out,
                                                      clip_path_out,
                                                      data)
        final_path = os.path.basename(final_path)
        return {"status": "COMPLETED",
                "final_path": final_path}
    except VideoException as exc:
        return {"status": "FAILED {0} to clip video ".format(
            os.path.basename(v_path))}
    except Exception as exc:
        return {"status": "FAILED {0} to clip video ".format(
            os.path.basename(v_path))}


# Rescale Video ->
# https://trac.ffmpeg.org/wiki/Scaling
@celery.task
def video_rescale(v_path, dir_v_path_out, base_name, data):
    try:
        final_path = video_manager.video_rescale(v_path, dir_v_path_out,
                                                 base_name, data)
        final_path = os.path.basename(final_path)
        return {"status": "COMPLETED",
                "final_path": final_path}
    except VideoException as exc:
        return {"status": "FAILED {0} to rescale video".format(
            os.path.basename(v_path))}
    except Exception as exc:
        return {"status": "FAILED {0} to rescale video".format(
            os.path.basename(v_path))}


"""Audio Tasks"""


# Transcode Audio clip
@celery.task
def audio_transcode(au_path, dir_v_path_out, base_name, audio_out_format):
    try:
        subprocess.call(['ffmpeg', '-i', au_path,
                         dir_v_path_out + '/' +  os.path.basename(base_name) +
                         "_audio_trancoded" +
                         audio_out_format])

        return {"status": "COMPLETED",
                "final_path": os.path.basename(base_name) +
                "_audio_trancoded" + audio_out_format}
    except Exception as exc:
        return {"status": "FAILED {0} to trancode audio".format(
            os.path.basename(au_path))}


# Clip Audio
@celery.task
def audio_clip(au_path, dir_v_path_out, base_name, data):
    try:
        from_clip = data["clip_audio"].split('to')[0]
        to_clip = data["clip_audio"].split('to')[1]
        subprocess.call(['ffmpeg', '-i', au_path, '-ss', from_clip,
                        '-to', to_clip,
                        dir_v_path_out + '/' + os.path.basename(
                        base_name) + "_clip_audio_From_To_" +
                        data["clip_audio"]
                        + data["audio_out_format"]])

        return {"status": "COMPLETED",
                "final_path": os.path.basename(
                    base_name) + "_clip_audio_From_To_"
                    + data["clip_audio"]
                    + data["audio_out_format"]}
    except Exception as exc:
        return {"status": "FAILED {0} to clip audio".format(
            os.path.basename(au_path))}


"""Image Tasks"""


# Image Transcode
@celery.task(bind=True)
def image_transcode(self, img_path, path,
                    image_out_format):
    try:
        img = Image.open(img_path)
        final_path = os.path.join(path, '{}{}'.format(
            os.path.basename(path),
            image_out_format))

        img.save(final_path)
        # no need to check path. if file is not save there will be an exception
        
        return {"status": "COMPLETED",
                "final_path": os.path.basename(path)}
    except Exception as exc:
        return "FAILED {0} to trancode image".format(
            os.path.basename(img_path))


# Crop Image
# "20:20:100:100
@celery.task
def image_crop(img_path, path, base_name, data):
    try:
        crop_dims = [int(x) for x in data["crop_image"].split(':') if x]
        img = Image.open(img_path)
        img2 = img.crop(
            (crop_dims[0], crop_dims[1], crop_dims[2], crop_dims[3]))

        final_path = os.path.join(path, os.path.basename(
                                    base_name) + "_Cropped_images_" + data[
                                    "crop_image"].replace(":", "-") + data[
                                    "image_out_format"])
        img2.save(final_path)
        return {"status": "COMPLETED",
                "final_path": os.path.basename(
                                    base_name) + "_Cropped_images_" + data[
                                    "crop_image"].replace(":", "-") + data[
                                    "image_out_format"]}
    except Exception as exc:
        return "FAILED {} to crop image".format(img_path)


# Resize Image
# 320x320
@celery.task
def image_resize(img_path, dir_v_path_out, base_name, data):
    try:
        img = Image.open(img_path)
        img2 = img.resize((int(data["resize_image"].split('x')[0]),
                           int(data["resize_image"].split('x')[1])))

        final_path = os.path.join(dir_v_path_out,
                                os.path.basename(base_name)
                                + "_Resized_" + data["resize_image"] + data[
                                "image_out_format"])
        img2.save(final_path)

        return {"status": "COMPLETED",
                                "final_path": os.path.basename(base_name)
                                + "_Resized_" + data["resize_image"] + data[
                                "image_out_format"]}
    except Exception as exc:
        return "FAILED {} to resize image".format(img_path)


def process_all_tasks(tasks, credentials, data):
    jobs = group(tasks)
    logger.info(jobs)
 
    result = jobs.apply_async()
    while not result.ready():
        logger.info('Waiting for results')
    with allow_join_result():
        synchronous = data.get("synchronous", False)
        results = result.get()
        if synchronous:
            with open(data['output_folder'] + '/' + 'data.txt',
            'w') as outfile:
                body = {
                'synchronous': 'False',
                'input_folder': data['input_folder'],
                'output_folder': data['output_folder'],
                'results': results
                }
                json.dump(body, outfile)
        else:
            add_result_to_amq(results, credentials, data)
        return results





def add_result_to_amq(results, credentials, data):
    print (results, credentials)

    username = credentials['brokerUsername']
    password = credentials['brokerPassword']
    queue = credentials['brokerQueue']
    host = credentials['brokerURL']
    port = credentials.get('brokerPort', 61613)
    conn = stomp.Connection([(host, port)])
    conn.connect(username, password, wait=True)
    body = {
        'synchronous':'False',
        'input_folder':data['input_folder'],
        'output_folder':data['output_folder'],
        'results':results
        }
    conn.send(body=json.dumps(body), destination=queue)
    time.sleep(2)
    conn.disconnect()
