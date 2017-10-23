from celery import Celery
import os
import warnings
import json
import subprocess
from subprocess import check_output
from os.path import isfile

broker="amqp://admin:mypass@broker:5672//"
celery = Celery("tasks", broker=broker)

#Celery Tasks

@celery.task
def convert_video_crop(dir_v_path_in, v_path, v_crop, dir_v_path_out, crop_path_out, data):
	subprocess.call(['ffmpeg', '-i', dir_v_path_in + '/' + v_path, '-filter:v', 'crop=' + v_crop, 
						'-c:a', 'copy', dir_v_path_out + '/' + crop_path_out + v_crop + '/' + crop_path_out + v_crop + data["v_out_format"]])
	#subprocess.call(['ffmpeg', '-i', dir_v_path_in + '/' + v_path, '-filter:v', 'crop=' + v_crop, '-c:a', 'copy', dir_v_path_out + '/' + new_dir + '/' + crop_path_out + v_crop + data["v_out_format"]])

@celery.task
def convert_video_frames(dir_v_path_in, v_path, dir_v_path_out, frame_path_out, base_name):
	subprocess.call(['ffmpeg', '-i', dir_v_path_in + '/' + v_path, '-r', '1'+'/'+'1', dir_v_path_out + '/' + base_name + "_Frames" + '/' + frame_path_out])

@celery.task
def convert_video_transcode(dir_v_path_in, v_path, dir_v_path_out, v_path_out, base_name):
	# Check the codec
	out = check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 
							'default=noprint_wrappers=1:nokey=1', dir_v_path_in + '/' + v_path])
	out = out.strip()
	if out == "mjpeg":
		subprocess.call(['ffmpeg', '-i', dir_v_path_in + '/' + v_path, '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', '-c:v', 
							'libx264', '-preset', 'veryslow', '-crf', '18', dir_v_path_out + '/' + base_name + "_transcoded" + '/' + v_path_out])
		# -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" 
		# in order to not have not scalling issues "height not visible by 2", because .h264 need even dimensions 
		# Divide the original height and width by 2, Round it down to the nearest pixel, Multiply it by 2 again, thus making it an even number
		# https://stackoverflow.com/questions/20847674/ffmpeg-libx264-height-not-divisible-by-2 and compress https://superuser.com/questions/1041075/what-is-the-best-way-to-losslessly-compress-mjpeg-to-mp4
	else:
		subprocess.call(['ffmpeg', '-y', '-i', dir_v_path_in + '/' + v_path, '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', '-q:a', 
							'100', dir_v_path_out + '/' + base_name + "_transcoded" + '/' + v_path_out])
	out = ""

@celery.task
def convert_video_rotate(dir_v_path_in, v_path, v_rotate, dir_v_path_out, rotate_path_out, base_name, data):
	subprocess.call(['ffmpeg', '-i', dir_v_path_in + '/' + v_path, '-vf', 
						'transpose=' + v_rotate, dir_v_path_out + '/' + base_name + '_ROTATED_' + data["rotate_video"] + '/' + rotate_path_out])

@celery.task
def convert_video_audio(dir_v_path_in, v_path, dir_v_path_out, a_path_out_wav):
	subprocess.call(['ffmpeg', '-y', '-i', dir_v_path_in + '/' + v_path, dir_v_path_out + '/' + a_path_out_wav])