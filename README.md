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

- **Input/output folders:**"/shared" as input_folder and output_folder. 
This a local folder into the container. The service uses default input folder ~/video_data.
The user may change this folder at the docker-compose.yaml file (volumes)

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

- **extract_audio:** Converts a video to .wav file format

- **extract_frames:** Extracts all the frames from the input video. Extracted frames are in .bmp format with a unique id.
