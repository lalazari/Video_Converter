# Video_Converter

## How to Run
1. Create Folder ~/converter
2. Create Folder ~/video_data
3. Copy your videos to ~/video_data
4. Install docker compose
5. Build images before starting containers: sudo docker-compose build
6. Start the containers in the background and leave them running: docker-compose up -d
   The docker-compose up command aggregates the output of each container.
	- Maybe you should also initialize the network using: sudo docker network create back-tier
7. `sudo curl -XPOST -H "Content-Type: application/json" -d '{..Parameters..}'`

## Curl Parameters

- **Input folder:**"/shared" as input_folder.
This a local folder into the container. The service uses default input folder ~/video_data.
The user may change this folder in the docker-compose.yaml file (volumes)

- **Output folder:**"/shared" as input_folder.
This is the output path for every type of conversion. Each operation keeps its directory tree in the output path. 
User can change this path by changing the output_folder parameter

- **file_type:** Checks if user wants to load only a specific type of files {Video,Images,Audio}

- **file_format:** Checks if user wants to load only a specific file format (Please check Supported Formats)

### Image Processing
- **image_out_format:** Image Transcode. Defines the output format of the image.
- **crop_image:** Crops down an image. Options are:
                
                Parameters-> The cropped rectangle, as a left:upper:right:lower.

				Example: 10:10:100:100

- **resize_image:** Returns a resized copy of this image in pixels. width **x** height.

### Audio Processing
- **audio_out_format:** Audio Transcode. Defines the output format of the audio files.

- **clip_audio:** Cuts a part of the audio file. 

                Parameters->
					Start: 00:00:00 - hours:minutes:seconds
					To / End : 00:00:00 - hours:minutes:seconds
				Example: 10to30
				Will cut a 20 seconds part from the input video (from 10th to 30th second).
				
### Video Processing
- **v_out_format:** The output format of the video. In order to convert a video, the user should also enable(true) the transcode_video parameter.
- **crop_video:** Crops down the input video. Where the options are as follows:

				Parameters-> out_w:out_h:x:y
					out_w is the width of the output rectangle
					out_h is the height of the output rectangle
					x and y specify the top left corner of the output rectangle

				Example: 80:60:200:100
				To crop a 80×60 section, starting from position (200, 100).
				Empty string("crop_video":"") means no crop

- **rotate_video:** Rotates the input video. Where the options are as follows:

				Parameters->
					0 = 90CounterCLockwise and Vertical Flip (default)
					1 = 90Clockwise
					2 = 90CounterClockwise
					3 = 90Clockwise and Vertical Flip

- **clip_video:** Cuts a part of the video (Video Clip)

				Parameters->
					Start: 00:00:00 - hours:minutes:seconds
					To / End : 00:00:00 - hours:minutes:seconds

				Example: 00:00:10to00:00:30
				Will cut a 20 seconds part from the input video (from 10th to 30th second).

- **extract_audio:** Converts a video to .wav file format.

- **extract_frames:** Extracts all the frames from the input video. Extracted frames are in .bmp format with a unique id.
				
				Parameters->
					0: Extract all frames. This results to a number = fps*Video_Duration
					Value (Milliseconds): Frames every "Value" Milliseconds with respect to fps 

## Asynchronous and synchronous execution:
Supports both synchronous and asynchronous execution.
- **Asynchronounous:** To activate asynchronous execution, the user should include **"asynchronous":True** in the curl post command. This module needs ActiveMQ credentials in order to return results to an ActiveMQ queue.
                
                Credentials->
    				"brokerInfo": {
                    "brokerURL": "amq",
                    "brokerUsername": "admin",
                    "brokerPassword": "admin",
                    "brokerQueue": "/test/queue/"
                }
    Results on ActiveMQ:
        `{"output_folder": "/shared/outputs", "input_folder": "/shared", "Asynchronous": "True", "results": [{"status": "FAILED Video1.mov to rotate video with parameter 1"}, {"status": "COMPLETED", "final_path": "Video2_ROTATED_1.wmv"]}`
The results could be checked at the http://localhost:8161/admin/queues.jsp .
- **Synchronous:** There is no need for ActiveMQ credentials. The results are saved to a unique Json file into the output directory.
## Example with curl

`curl -XPOST -H "Content-Type: application/json" -d '{"input_folder":"/shared","output_folder":"/shared/outputs","file_type":"","file_format":"",
"image_out_format":".tiff","crop_image":"10:10:100:100","resize_image":"25x25","audio_out_format":".aac",
"clip_audio":"10to20","v_out_format":".avi","crop_video":"80:60:200:100","rotate_video":"0",
"clip_video":"00:00:10to00:00:30","extract_frames":"0","transcode_video":false,"extract_audio":false,"brokerInfo": { "brokerURL": "amq", "brokerUsername": "admin", "brokerPassword": "admin", "brokerQueue": "/test/queue/"}}' localhost:9877/`
