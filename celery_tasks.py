from celery import Celery
import os
import warnings
import json
import subprocess
from subprocess import check_output
from os.path import isfile
from celery.utils.log import get_task_logger
from PIL import Image

broker="amqp://admin:mypass@broker:5672//"
# CELERY_RESULT_BACKEND ='amqp://admin:mypass@broker:5672//'
# broker_api = "amqp://admin:mypass@broker:15672/api/"
celery = Celery("tasks", backend=broker, broker=broker)#, worker_send_task_events = True, event_queue_expires = 240)

#Celery Tasks
"""Video Tasks"""

# Cropping Video Task
@celery.task
def convert_video_crop(v_path, v_crop, dir_v_path_out, crop_path_out, data):
	try:
		subprocess.call(['ffmpeg', '-i', v_path, '-filter:v', 'crop=' + v_crop, 
				'-c:a', 'copy', dir_v_path_out + '/' + crop_path_out + v_crop + '/'
				 +  os.path.basename(crop_path_out) + v_crop + data["v_out_format"]])

		if os.path.isfile( dir_v_path_out + '/' + crop_path_out + v_crop + '/'
			+  os.path.basename(crop_path_out) + v_crop + data["v_out_format"]):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

logger = get_task_logger(__name__)

# Convert video to frames
@celery.task
def convert_video_frames(v_path, dir_v_path_out, frame_path_out, base_name, data):

	try:
		fps = check_output(['ffprobe', '-v', '0', '-of', 'csv=p=0', '-select_streams', '0', '-show_entries', 'stream=r_frame_rate', v_path])
		fps = fps.strip()
		fps = fps.split('/')[0]
		"""If input is 0 then extract all frames. This results to fps*secs(video_duration) number of frames"""
		if data["extract_frames"] == '0':
			subprocess.call(['ffmpeg', '-i', v_path, '-r', fps, dir_v_path_out + '/'
			 + base_name + "_Frames" + '/' + os.path.basename(base_name) + '%03d' + '.bmp'])
		
		else:
			i_fps = float(data["extract_frames"])
			i_fps = 1000/float(i_fps)
			r = float(i_fps)

			if float(i_fps) <= float(fps):
				subprocess.call(['ffmpeg', '-i', v_path, '-r', str(r), dir_v_path_out + '/' 
					+ base_name + "_Frames" + '/' + os.path.basename(base_name) + '%03d' + '.bmp'])
			else:	
			  	subprocess.call(['ffmpeg', '-i', v_path, '-r', fps, dir_v_path_out + '/'
			  	 + base_name + "_Frames" + '/' + os.path.basename(base_name) + '%03d' + '.bmp'])

		if os.path.isfile( dir_v_path_out + '/' 
			+ base_name + "_Frames" + '/' + os.path.basename(base_name) + '001' + '.bmp'):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

# Transcode Video
@celery.task
def convert_video_transcode(v_path, dir_v_path_out, base_name, v_out_format):
	# Check the codec
	try:
		out = check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 
			'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', v_path])

		out = out.strip()
		if out == "mjpeg":
			subprocess.call(['ffmpeg', '-i', v_path, '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', '-c:v', 
					'libx264', '-preset', 'veryslow', '-crf', '18', dir_v_path_out + '/' + base_name + "_transcoded"
					 + '/' + os.path.basename(base_name) + '_transcoded' + v_out_format])

			# -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" 
			# in order to not have not scalling issues "height not visible by 2", because .h264 need even dimensions 
			# Divide the original height and width by 2, Round it down to the nearest pixel, Multiply it by 2 again, thus making it an even number
			# https://stackoverflow.com/questions/20847674/ffmpeg-libx264-height-not-divisible-by-2 and 
			# compress https://superuser.com/questions/1041075/what-is-the-best-way-to-losslessly-compress-mjpeg-to-mp4
		else:
			subprocess.call(['ffmpeg', '-y', '-i', v_path, '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', '-q:a', 
					'100', dir_v_path_out + '/' + base_name + "_transcoded" + '/' + os.path.basename(base_name) + '_transcoded' + v_out_format])

		if os.path.isfile( dir_v_path_out + '/' + base_name + "_transcoded"
			+ '/' + os.path.basename(base_name) + '_transcoded' + v_out_format):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"
# Rotate Video
@celery.task
def convert_video_rotate(v_path, v_rotate, dir_v_path_out, base_name, data):
	try:
		subprocess.call(['ffmpeg', '-i', v_path, '-vf', 
				'transpose=' + v_rotate, dir_v_path_out + base_name + '_ROTATED_' + data["rotate_video"] + '/'
				 + os.path.basename(base_name) + '_ROTATED_' + data["rotate_video"] + data["v_out_format"]])

		if os.path.isfile( dir_v_path_out + base_name + '_ROTATED_' + data["rotate_video"] + '/'
				 + os.path.basename(base_name) + '_ROTATED_' + data["rotate_video"] + data["v_out_format"]):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

# Extract Audio
@celery.task
def convert_video_audio(dir_v_path_in, v_path, dir_v_path_out, a_path_out_wav):
	try:
		subprocess.call(['ffmpeg', '-y', '-i', dir_v_path_in + '/' + v_path, dir_v_path_out + '/' + a_path_out_wav])

		if os.path.isfile( dir_v_path_out + '/' + a_path_out_wav):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

# Clip Video
@celery.task
def convert_video_clip(v_path, dir_v_path_out, clip_path_out, data):
	try:
		from_clip = data["clip_video"].split('to')[0]
		to_clip = data["clip_video"].split('to')[1]
		subprocess.call(['ffmpeg', '-i',  v_path, '-vcodec', 'copy', '-acodec', 'copy', '-ss', from_clip,
		 '-to', to_clip, dir_v_path_out + clip_path_out +'/'+ os.path.basename(clip_path_out) + data["v_out_format"] ])

		if os.path.isfile( dir_v_path_out + clip_path_out +'/'+ os.path.basename(clip_path_out) + data["v_out_format"]):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

# Rescale Video -> 
#https://trac.ffmpeg.org/wiki/Scaling
@celery.task
def video_rescale(v_path, dir_v_path_out, base_name, data):
	try:
		subprocess.call(['ffmpeg', '-i',  v_path, '-vf', 'scale='+str(data["rescale_video"]),
			dir_v_path_out + base_name + "rescale_To_" + data["rescale_video"] +'/'
			+ os.path.basename(base_name) + "rescale_To_" + data["rescale_video"] + data["v_out_format"] ])

		if os.path.isfile( dir_v_path_out + base_name + "rescale_To_" + data["rescale_video"] +'/'
			+ os.path.basename(base_name) + "rescale_To_" + data["rescale_video"] + data["v_out_format"]):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"


"""Audio Tasks"""

# Transcode Audio clip
@celery.task
def audio_transcode(au_path, dir_v_path_out, base_name, audio_out_format):
	try:
		subprocess.call(['ffmpeg', '-i', au_path, dir_v_path_out + '/' + base_name + "_audio_trancoded_" + '/'
		 + os.path.basename(base_name) + '_audio_transcoded' + audio_out_format])

		if os.path.isfile( dir_v_path_out + '/' + base_name + "_audio_trancoded_" + '/'
		 + os.path.basename(base_name) + '_audio_transcoded' + audio_out_format):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

# Clip Audio
@celery.task
def audio_clip(au_path, dir_v_path_out, base_name, data):
	try:
		from_clip = data["clip_audio"].split('to')[0]
		to_clip = data["clip_audio"].split('to')[1]
		subprocess.call(['ffmpeg', '-i',  au_path, '-ss', from_clip,
		 '-to', to_clip, dir_v_path_out + base_name + "_clip_audio_From_To_" + data["clip_audio"]  +'/'
		 + os.path.basename(base_name) +  "_clip_audio_From_To_" + data["clip_audio"] + data["audio_out_format"] ])

		if os.path.isfile(dir_v_path_out + base_name + "_clip_audio_From_To_" + data["clip_audio"]  +'/'
		 + os.path.basename(base_name) +  "_clip_audio_From_To_" + data["clip_audio"] + data["audio_out_format"]):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

"""Image Tasks"""
# Image Transcode
@celery.task(bind=True)
def image_transcode(self,img_path, dir_v_path_out, base_name, image_out_format):
	#path = img_path.rsplit('/',1)[0]
	try:
		img = Image.open(img_path)
		img.save( dir_v_path_out + '/' + base_name + "_image_trancoded_" + '/' +  os.path.basename(base_name) + "_image_trancoded_"  + image_out_format)
		if os.path.isfile(dir_v_path_out + '/' + base_name + "_image_trancoded_" + '/' +  os.path.basename(base_name) + "_image_trancoded_"  + image_out_format):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"

# Crop Image
#"20:20:100:100
@celery.task
def image_crop(img_path, dir_v_path_out, base_name, data):

	try:
		crop_dims = [int(x) for x in data["crop_image"].split(':') if x]
		#crop_dims = int(crop_dims)
		img = Image.open(img_path)
		img2 = img.crop((crop_dims[0], crop_dims[1], crop_dims[2], crop_dims[3]))
		img2.save(dir_v_path_out + '/' + base_name + "_Cropped_images_" + data["crop_image"].replace(":","-") + '/'
		 +  os.path.basename(base_name) +  "_Cropped_images_" + data["crop_image"].replace(":","-") + data["image_out_format"] )

		if os.path.isfile(dir_v_path_out + '/' + base_name + "_Cropped_images_" + data["crop_image"].replace(":","-") + '/'
		 +  os.path.basename(base_name) +  "_Cropped_images_" + data["crop_image"].replace(":","-") + data["image_out_format"]):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"


# Resize Image
#320x320
@celery.task
def image_resize(img_path, dir_v_path_out, base_name, data):
	try:
		img = Image.open(img_path)
		img2 = img.resize((int(data["resize_image"].split('x')[0]),int(data["resize_image"].split('x')[1])))
		img2.save(dir_v_path_out + '/' + base_name + "_Resized_images_" + data["resize_image"].replace("x","-") + '/'
		 +  os.path.basename(base_name) +  "_Resized_images_" + data["resize_image"].replace("x","-") + data["image_out_format"] )

		if os.path.isfile(dir_v_path_out + '/' + base_name + "_Resized_images_" + data["resize_image"].replace("x","-") + '/'
		 +  os.path.basename(base_name) +  "_Resized_images_" + data["resize_image"].replace("x","-") + data["image_out_format"]):
			return "COMPLETED"
	except Exception as exc:
		return "FAILED"