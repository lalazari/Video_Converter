import web
import sys, os
import warnings
import json
import subprocess
from os.path import isfile
from DatabaseConnection import DatabaseConnection

# Celery: Tasks/job queue,
# Send/Receive message solution (broker) -> Rabbitmq (See docker-compose.yaml)
from celery_tasks import convert_video_crop,convert_video_frames,convert_video_transcode,convert_video_rotate,convert_video_audio,convert_video_clip

warnings.simplefilter('ignore')

urls = (
    '/(.*)', 'Service'
)
app = web.application(urls, globals())

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
        data = web.data()
        data = json.loads(data)

        ###dbconn = DatabaseConnection(data)


        #dbconn.save({"user": data["mongodb"]["username"], "user2":"papa"})

        #data["mongodb"]["username"]

        dir_v_path_in = data["input_folder"]
        dir_v_path_out = data["output_folder"]
        videotypes = ['.mp4', '.avi', '.wmv', '.3gp', '.flv', '.mkv', '.mpg', '.mpeg', '.ogv',
                        '.ogg', '.mov', '.qt', '.ts', '.TOD', '.MOD', '.dv4', '.h264', '.vid', '.ssf', '.sec']
        namelist = [fn for fn in os.listdir(dir_v_path_in)
                if any(fn.endswith(ext) for ext in videotypes)]

        if not os.path.exists(dir_v_path_out):
                os.makedirs(dir_v_path_out)

        response = {'input_folder': dir_v_path_in, 'output_folder': dir_v_path_out}
        processed = []
        for v_path in namelist:
            base_name = os.path.splitext(v_path)[0]
            #if isfile(dir_v_path_out + '/' + v_path_out):
                    #v_path_out = base_name + '_transcoded' #+  #'_transcoded.mp4'
            #a_path_out = base_name + '.mp3'

            # Video Convertion
            v_path_out = base_name + '_transcoded' + data["v_out_format"]
            # Create Frames, unique output name for each frame
            frame_path_out = base_name + '%03d' + '.bmp' # for the frames
            # Crop Video
            crop_path_out = base_name + '_CROPPED_' #+ data["v_out_format"]
            # Rotate Video
            rotate_path_out = base_name + '_ROTATED_' + data["rotate_video"] + data["v_out_format"]
            # Audio Convertion
            a_path_out_wav = base_name + '.wav'
            # Video Clip / Cut part of Video
            clip_path_out = base_name + "_Cut_From_To" + data["clip_video"]# + data["v_out_formtat"]


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

            v_clip_video = ""
            if "clip_video" in data:
                v_clip_video = data["clip_video"]

            a_video = {'input_video': v_path}

            # Delay method is needed if we want to process the task asynchronously.
            if v_crop:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + '/' + crop_path_out + v_crop])
                convert_video_crop.delay(dir_v_path_in, v_path, v_crop, dir_v_path_out, crop_path_out, data)
                a_video["output_crop"] = crop_path_out + v_crop + data["v_out_format"]
                #dbconn.save({"User": data["mongodb"]["username"], "Action":"Video_crop", "Parameters":data["crop_video"], "Input_Video":base_name})
            if v_extract_frames:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + '/' + base_name + "_Frames" ])
                convert_video_frames.delay(dir_v_path_in, v_path, dir_v_path_out, frame_path_out, base_name, data)
                a_video["output_frames"] = frame_path_out
                #dbconn.save({"User": data["mongodb"]["username"], "Action":"Frame_Extraction", "Parameters":data["extract_frames"], "Input_Video":base_name})
            if v_transcode:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + '/' + base_name + "_transcoded"])
                convert_video_transcode.delay(dir_v_path_in, v_path, dir_v_path_out, v_path_out, base_name)
                a_video["output_video"] = v_path_out
                #dbconn.save({"User": data["mongodb"]["username"], "Action":"Transcode_video", "Parameters":data["v_out_format"], "Input_Video":base_name})
            if v_rotate:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + '/' + base_name + '_ROTATED_' + data["rotate_video"]])
                convert_video_rotate.delay(dir_v_path_in, v_path, v_rotate, dir_v_path_out, rotate_path_out, base_name, data)
                a_video["output_rotate"] = rotate_path_out
                #dbconn.save({"User": data["mongodb"]["username"], "Action":"Rotate_Video", "Parameters":data["rotate_video"], "Input_Video":base_name})
            if v_extract_audio:
                convert_video_audio.delay(dir_v_path_in, v_path, dir_v_path_out, a_path_out_wav)
                a_video["output_audio"] = a_path_out_wav
                #dbconn.save({"User": data["mongodb"]["username"], "Action":"Audio_Extraction", "Parameters":data["extract_audio"], "Input_Video":base_name})
            if v_clip_video:
                make_dir = subprocess.call(['mkdir', dir_v_path_out + '/' + clip_path_out])
                convert_video_clip.delay(dir_v_path_in, v_path, dir_v_path_out, clip_path_out, base_name, data)
                a_video["output_clip"] = clip_path_out + data["v_out_format"]
                #dbconn.save({"User": data["mongodb"]["username"], "Action":"Clip_Video", "Parameters":data["clip_video"], "Input_Video":base_name})

            processed.append(a_video)

        response['processed'] = processed

        jsonstr = json.dumps(response)

        return jsonstr

if __name__ == "__main__":
    app.run()

