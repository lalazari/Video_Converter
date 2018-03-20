import web
import sys, os
import warnings
import json
import subprocess
from os.path import isfile
from DatabaseConnection import DatabaseConnection
import logging
import coloredlogs
import filecmp
from celery.result import AsyncResult

# Celery: Tasks/job queue,
# Send/Receive message solution (broker) -> Rabbitmq (See docker-compose.yaml)
from celery_tasks import (convert_video_crop,convert_video_frames,convert_video_transcode,convert_video_rotate,convert_video_audio,
    convert_video_clip, audio_transcode, audio_clip, image_transcode, image_crop, image_resize, video_rescale)


"""Supported File Format types"""
videotypes = ['mp4', 'avi', 'wmv', '3gp', 'flv', 'mkv', 'mpg', 'mpeg', 'ogv',
                 'ogg', 'mov', 'qt', 'ts', 'TOD', 'MOD', 'dv4', 'h264', 'vid', 'ssf', 'sec']

imagetypes = ['jpeg','jpg','jif','jfif','png','pdf','tif','tiff','gif']

audiotypes = ['wav','mp3','aac','aiff','wma','flac']


"""All results goes to the output foler, keeping its subdirectories"""
output_path = '/home/lazlazar/Desktop/Eketa/Video_converter/video_data/outputs'

"""All images, videos, audio have been found at the input directory"""
all_images = []
all_videos = []
all_audio = []

responses_images = {}
responses_audio = {}
responses_video ={}

warnings.simplefilter('ignore')

urls = (
    '/(.*)', 'Service'
)

logger = logging.getLogger(__name__)

app = web.application(urls, globals(), logger)

class Service:
    def GET(self, name):
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin',      '*')
        web.header('Access-Control-Allow-Credentials', 'true')
        return json.dumps({'message': 'OK!'})
    def POST(self, name):
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin',      '*')
        web.header('Access-Control-Allow-Credentials', 'true')

        coloredlogs.install(level='DEBUG', logger=logger)

        data = web.data()
        data = json.loads(data)

        
        """This part checks what parameters are included in the .json """

        #If mongodb is included
        if "mongodb" in data:
            dbconn = DatabaseConnection(data)
        else:
            dbconn = None
        #dbconn.save({"user": data["mongodb"]["username"], "user2":"papa"})
        #data["mongodb"]["username"]

        """Check if user provides input and output paths"""
        if "input_folder" in data:
            dir_v_path_in = data["input_folder"]
        else:
           dir_v_path_in = "/shared" 

        if "output_folder" in data:
            dir_v_path_out = data["output_folder"]
        else:
            dir_v_path_out = "/shared/outputs" 

        logger.info("In Path: " + str(dir_v_path_in))
        logger.info("Out Path: " + str(dir_v_path_out))

        """This is the output path of every type of conversion. Each operation keeps its directory tree inside the output path. 
        User can change this path by changing the output_folder parameter"""
        if not os.path.exists(dir_v_path_out):
                os.makedirs(
                    )


        """Supported File types"""
        """Check if user wants to load only a type of files {Video,Images,Audio}"""
        if "file_type" in data:
            type_of_file = data["file_type"]
        else:
            type_of_file = "default"

        """Check if user wants a specidic file format"""
        if "file_format" in data:
            f_format = data["file_format"]
        else:
            f_format = "default"

        """Find any type of files (Default) or user requested types"""
        try:
            find_files(dir_v_path_in, logger= logger, type_of_file=type_of_file, f_format=f_format, dir_v_path_out=dir_v_path_out)
        except:
            logger.error("Wrong input Error")



        response = {'input_folder': dir_v_path_in, 'output_folder': dir_v_path_out}
        processed = []

        if all_videos:
            video_processing(processed, data, dir_v_path_in, dir_v_path_out, dbconn)
        if all_audio:
            audio_processing(processed, data, dir_v_path_in, dir_v_path_out, dbconn)
        if all_images:
            image_processing(processed, data, dir_v_path_in, dir_v_path_out, dbconn)

        response['processed'] = processed

        jsonstr = json.dumps(response)

        return jsonstr

def find_files(path_in, logger, type_of_file, f_format, dir_v_path_out):


    if (type_of_file in "default") and (f_format in "default"):
        for path, subdirs, files in os.walk(path_in):
            for name in files:
                if any([name.split('.')[1] in videotypes]):
                    all_videos.append(str(os.path.join(path, name)))
                elif any([name.split('.')[1] in imagetypes]):
                    all_images.append(str(os.path.join(path, name)))
                elif any([name.split('.')[1] in audiotypes]):
                    all_audio.append(str(os.path.join(path, name)))

    elif type_of_file in ['Images','images']:
        if f_format in "default":
            for path, subdirs, files in os.walk(path_in):
                for name in files:
                    if any([name.split('.')[1] in imagetypes]):
                        all_images.append(str(os.path.join(path, name)))
        else:
            for path, subdirs, files in os.walk(path_in):
                for name in files:
                    if any([name.split('.')[1] in str(f_format)]):
                        all_images.append(str(os.path.join(path, name)))

    elif type_of_file in ['Video','video']:
        if f_format in "default":
            for path, subdirs, files in os.walk(path_in):
                for name in files:
                    if any([name.split('.')[1] in videotypes]):
                        all_videos.append(str(os.path.join(path, name)))
        else:
            for path, subdirs, files in os.walk(path_in):
                for name in files:
                    if any([name.split('.')[1] in f_format]):
                        all_videos.append(str(os.path.join(path, name)))

    elif type_of_file in ['Audio','audio']:
        if f_format in "default":
            for path, subdirs, files in os.walk(path_in):
                for name in files:
                    if any([name.split('.')[1] in audiotypes]):
                        all_audio.append(str(os.path.join(path, name)))
        else:
            for path, subdirs, files in os.walk(path_in):
                for name in files:
                    if any([name.split('.')[1] in f_format]):
                        all_audio.append(str(os.path.join(path, name)))

    for path, subdirs, files in os.walk(path_in):
        logger.info("sudirs " + str(path))
        logger.info("dir_v_path_out " + str(dir_v_path_out))

        if os.path.samefile(path, dir_v_path_out):
            continue
        else:
            make_dir = subprocess.call(['mkdir', dir_v_path_out + path])

    logger.info("Video: " + str(all_videos))
    logger.info("Images: " + str(all_images))
    logger.info("Audio: " + str(all_audio))


def image_processing(processed, data, dir_v_path_in, dir_v_path_out, dbconn):
    need_check = False
    for img_path in all_images:
        base_name = os.path.splitext(img_path)[0]
        logger.info("Base name Image " + str(base_name))

        a_image = {'input_image': img_path}

        if need_check:
            data["image_out_format"] = os.path.splitext(img_path)[1]

        if ("image_out_format" not in data) or (data["image_out_format"] in ""):
            data["image_out_format"] = os.path.splitext(img_path)[1]
            need_check = True
        from celery.execute import send_task
        if data["image_out_format"] not in os.path.splitext(img_path)[1]:
            if not os.path.isdir(dir_v_path_out + base_name + "_image_trancoded_"):
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "_image_trancoded_"])
            res_img_trans = image_transcode.delay(img_path, dir_v_path_out, base_name, data["image_out_format"])
            res_img_trans.get()

            responses_images[img_path + '_transcode'] = res_img_trans.result

            a_path_out = base_name + "_image_trancoded_" + data["image_out_format"]
            a_image["output_image"] = a_path_out

        logger.info("FORMAT IMAGE " + str(data["image_out_format"]))

        if ("crop_image" in data) and (data["crop_image"] not in ""):
            if not os.path.isdir(dir_v_path_out + base_name + "_Cropped_images_"):
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "_Cropped_images_" + data["crop_image"].replace(":","-")])
            res_img_crop = image_crop.delay(img_path, dir_v_path_out, base_name, data)

            res_img_crop.get()
            responses_images[img_path + '_crop_image'] = res_img_crop.result

            a_image["image_crop"] = base_name + "_Cropped_images_" + data["crop_image"].replace(":","-") + data["image_out_format"]

        if ("resize_image" in data) and (data["resize_image"] not in ""):
            if not os.path.isdir(dir_v_path_out + base_name + "_Resized_images_"):
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "_Resized_images_" + data["resize_image"].replace("x","-")])
            res_img_resize = image_resize.delay(img_path, dir_v_path_out, base_name, data)
            res_img_resize.get()
            responses_images[img_path + '_resize_image'] = res_img_resize.result
            a_image["image_resize"] = base_name + "_Resized_images_" + data["resize_image"].replace("x","-") + data["image_out_format"]

        processed.append(a_image)

    logger.info("Image Response" + str(responses_images))


def audio_processing(processed, data, dir_v_path_in, dir_v_path_out, dbconn):

    for au_path in all_audio:
        base_name = os.path.splitext(au_path)[0]
        logger.info("Base name Audio " + str(base_name))

        a_audio = {'input_audio': au_path}

        if ("audio_out_format" not in data) or (data["audio_out_format"] in ""):
            data["audio_out_format"] = os.path.splitext(au_path)[1]

        logger.info("AUDIO FORMAT " + str(data["audio_out_format"]))
        if data["audio_out_format"] not in os.path.splitext(au_path)[1]:
            if not os.path.isdir(dir_v_path_out + base_name + "_audio_trancoded_"):
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "_audio_trancoded_"])
                res_audio_trans = audio_transcode.delay(au_path, dir_v_path_out, base_name, data["audio_out_format"])
                res_audio_trans.get()
                responses_audio[au_path + '_transpose'] = res_audio_trans.result
                a_path_out = base_name + "_audio_trancoded_" + data["audio_out_format"]
                a_audio["output_audio"] = a_path_out

        logger.info("FORMAT AUDIO " + str(data["audio_out_format"]))

        if (("clip_audio" in data) and (data["clip_audio"] not in "")):
            if not os.path.isdir(dir_v_path_out + base_name + "_clip_audio_From_To_" + data["clip_audio"]):
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "_clip_audio_From_To_" + data["clip_audio"]])
                res_audio_clip = audio_clip.delay(au_path, dir_v_path_out, base_name, data)
                res_audio_clip.get()
                responses_audio[au_path + '_audio_clip'] = res_audio_clip.result
                a_audio["output_clip"] = base_name + "_clip_audio_From_To_" + data["clip_audio"] + data["audio_out_format"]


        processed.append(a_audio)

    logger.info("Audio Response" + str(responses_audio))

def video_processing(processed,data, dir_v_path_in, dir_v_path_out, dbconn):
    for v_path in all_videos:

            base_name = os.path.splitext(v_path)[0]
            logger.info("Base NAME " + str(base_name))

            if "v_out_format" not in data:
                video_format = os.path.splitext(v_path)[1]
                data["v_out_format"]=video_format

            if "rotate_video" in data:
                # Rotate Video
                rotate_path_out = base_name + '_ROTATED_' + data["rotate_video"] + data["v_out_format"]
                logger.info("Rotate Path " + str(rotate_path_out))

            v_clip_video = ""
            if "clip_video" in data:
                # Video Clip / Cut part of Video
                v_clip_video = data["clip_video"]
                data_clip_video = data["clip_video"].replace(":","-")
                clip_path_out = base_name + "_Cut_From_To" + data_clip_video
                logger.info("Clip Path " + str(clip_path_out))



            # Video Convertion
            v_path_out = base_name + '_transcoded' + data["v_out_format"]
            logger.info("V_PATH OUT  " + str(v_path_out))
            # Create Frames, unique output name for each frame
            frame_path_out = base_name + '%03d' + '.bmp' # for the frames
            # Crop Video
            crop_path_out = base_name + '_CROPPED_' #+ data["v_out_format"]
           
            # Audio Convertion
            a_path_out_wav = base_name + '.wav'
            

            v_crop = ""
            if "crop_video" in data:
                v_crop = data["crop_video"]
                
            v_extract_frames = ""
            if "extract_frames" in data:
                v_extract_frames = data["extract_frames"]
                
            v_transcode = False
            if "transcode_video" in data:
                    v_transcode = data["transcode_video"]

            v_rotate = ""
            if "rotate_video" in data:
                v_rotate = data["rotate_video"]

            v_extract_audio = False
            if "extract_audio" in data:
                v_extract_audio = data["extract_audio"]

            a_video = {'input_video': v_path}

            # Delay method is needed if we want to process the task asynchronously.
            if v_crop:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + crop_path_out + v_crop])
                res_video_crop = convert_video_crop.delay(v_path, v_crop, dir_v_path_out, crop_path_out, data)
                res_video_crop.get()
                responses_video[v_path + '_crop_video'] = res_video_crop.result
                a_video["output_crop"] = crop_path_out + v_crop + data["v_out_format"]
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"], "Action":"Video_crop", "Parameters":data["crop_video"], "Input_Video":base_name})
            if v_extract_frames:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "_Frames" ])
                res_video_frames = convert_video_frames.delay(v_path, dir_v_path_out, frame_path_out, base_name, data)
                res_video_frames.get()
                responses_video[v_path + '_frames'] = res_video_frames.result
                a_video["output_frames"] = frame_path_out
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"], "Action":"Frame_Extraction", "Parameters":data["extract_frames"], "Input_Video":base_name})
            if v_transcode:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "_transcoded"])
                res_video_transcode = convert_video_transcode.delay(v_path, dir_v_path_out, base_name, data["v_out_format"])
                res_video_transcode.get()
                responses_video[v_path + '_video_trans'] = res_video_transcode.result
                a_video["output_video"] = v_path_out
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"], "Action":"Transcode_video", "Parameters":data["v_out_format"], "Input_Video":base_name})
            if v_rotate:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + '_ROTATED_' + data["rotate_video"]])
                res_video_rotate = convert_video_rotate.delay(v_path, v_rotate, dir_v_path_out, base_name, data)
                res_video_rotate.get()
                responses_video[v_path + '_video_rotate'] = res_video_rotate.result
                a_video["output_rotate"] = rotate_path_out
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"], "Action":"Rotate_Video", "Parameters":data["rotate_video"], "Input_Video":base_name})

            if v_extract_audio:
                res_video_audio = convert_video_audio.delay(dir_v_path_in, v_path, dir_v_path_out, a_path_out_wav)
                res_video_audio.get()
                responses_video[v_path + '_video_audio'] = res_video_audio.result
                a_video["output_audio"] = a_path_out_wav
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"], "Action":"Audio_Extraction", "Parameters":data["extract_audio"], "Input_Video":base_name})


            if v_clip_video:
                logger.info("CREATE DIR " + str(dir_v_path_out) + "    " + str(clip_path_out))
                make_dir = subprocess.call(['mkdir', dir_v_path_out + clip_path_out])
                res_video_clip = convert_video_clip.delay(v_path, dir_v_path_out, clip_path_out, data)
                res_video_clip.get()
                responses_video[v_path + '_video_clip'] = res_video_clip.result
                a_video["output_clip"] = clip_path_out + data["v_out_format"]
                if dbconn is not None:
                    dbconn.save({"User": data["mongodb"]["username"], "Action":"Clip_Video", "Parameters":data["clip_video"], "Input_Video":base_name})

            if ("rescale_video" in data) and (data["rescale_video"] not in ""):
                logger.info("Rescale Parameters " + str(data["rescale_video"]))
                if not os.path.isdir(dir_v_path_out + base_name + "rescale_To_" + data["rescale_video"]):
                    make_dir = subprocess.call(['mkdir', dir_v_path_out + base_name + "rescale_To_" + data["rescale_video"]])
                    res_video_rescale = video_rescale.delay(v_path, dir_v_path_out, base_name, data)
                    res_video_rescale.get()
                    responses_video[v_path + '_video_rescale'] = res_video_rescale.result
                    a_video["rescaled_video"] = base_name + "rescale_To_" + data["rescale_video"] + data["v_out_format"]


            processed.append(a_video)

    logger.info("Video Response" + str(responses_video))

if __name__ == "__main__":

    coloredlogs.install(level='DEBUG', logger=logger)
    app.run()
    responses_images = json.dumps(responses_images)
    responses_audio = json.dumps(responses_audio)
    responses_video = json.dumps(responses_video)

    del all_images[:] 
    del all_videos[:] 
    del all_audio[:]

    responses_images = {}
    responses_audio = {}
    responses_video ={}

#sudo curl -XPOST -H "Content-Type: application/json" -d '{"input_folder":"/shared","output_folder":"/shared/outputs","v_out_format":".avi","crop_video":"","rotate_video":"","clip_video":"00:00:10to00:00:30","image_out_format":".makis","transcode_video":false,"extract_audio":false,"extract_frames":false}' localhost:9877/


#sudo curl -XPOST -H "Content-Type: application/json" -d '{"input_folder":"/shared","output_folder":"/shared/outputs","file_type":"","file_format":"","image_out_format":"","crop_image":"","resize_image":"","audio_out_format":"","clip_audio":"","v_out_format":".avi","crop_video":"","rotate_video":"","clip_video":"00:00:10to00:00:30","extract_frames":"","transcode_video":false,"extract_audio":false,"extract_frames":false}' localhost:9877/

# sudo curl -XPOST -H "Content-Type: application/json" -d '{"input_folder":"/shared","output_folder":"/shared/outputs","file_type":"images","file_format":"","image_out_format":".tiff","crop_image":"","resize_image":"","audio_out_format":"","clip_audio":"","v_out_format":".avi","crop_video":"","rotate_video":"","clip_video":"00:00:10to00:00:30","extract_frames":"","transcode_video":false,"extract_audio":false,"extract_frames":false}' localhost:9877/
# all -> sudo curl -XPOST -H "Content-Type: application/json" -d '{"input_folder":"/shared","output_folder":"/shared/outputs","file_type":"","file_format":"","image_out_format":".tiff","crop_image":"10:10:100:100","resize_image":"25x25","audio_out_format":".aac","clip_audio":"10to20","v_out_format":".avi","crop_video":"80:60:200:100","rotate_video":"0","clip_video":"00:00:10to00:00:30","extract_frames":"0","transcode_video":false,"extract_audio":false,"extract_frames":false}' localhost:9877/
