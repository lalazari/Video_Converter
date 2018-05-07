import json
import logging
from multiprocessing import Process
import warnings

import coloredlogs
import web

# Celery: Tasks/job queue,
# Send/Receive message solution (broker) -> Rabbitmq (See docker-compose.yaml)
from file_manager import FileManager
from process_manager import ProcessManager
from serializer import Serializer
from utils import mkdir_p

"""All results goes to the output foler, keeping its subdirectories"""
output_path = '/home/lazlazar/Desktop/Eketa/Video_converter/video_data/outputs'

warnings.simplefilter('ignore')

urls = (
    '/(.*)', 'Service'
)

logger = logging.getLogger('web')

app = web.application(urls, globals(), logger)


class Service(object):
    def GET(self, name):
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')
        return json.dumps({'message': 'OK!'})

    def POST(self, name):
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')

        coloredlogs.install(level='DEBUG', logger=logger)

        data = web.data()
        data = json.loads(data)

        logger.info("Got request data{}".format(data))

        serializer = Serializer()
        # Get data from serializer here

        serializer.serialize(data)

        active_q_credentials = data.get('brokerInfo')

        input_folder = serializer.input_folder
        output_folder = serializer.output_folder

        logger.info("In Path: " + str(input_folder))
        logger.info("Out Path: " + str(output_folder))

        """This is the output path for every type of conversion. Each operation keeps its directory
        tree inside the output path. 
        User can change this path by changing the output_folder parameter"""
        mkdir_p(output_folder)

        file_type = serializer.file_type
        file_format = serializer.file_format

        """Find any type of files (Default) or user requested types"""
        try:
            logger.info(
                "Getting files from manager:"
                "input_folder [{}]"
                " type of file[{}],"
                " file_format [{}], "
                "output_folder[{}]".format(input_folder,
                                           file_type,
                                           file_format,
                                           output_folder))
            file_manager = FileManager()
            file_manager.find_files(input_folder,
                                    logger=logger,
                                    type_of_file=file_type,
                                    f_format=file_format,
                                    dir_v_path_out=output_folder)
        except Exception as e:
            msg = "Wrong input Error {}".format(e.message)
            logger.error(msg)
            return json.dumps({"error": msg})

        response = {'input_folder': input_folder, 'output_folder': output_folder}

        process_manager = ProcessManager(active_q_credentials,
                                         file_manager)

        if file_manager.all_videos:
            process_manager.video_processing(data, input_folder,
                                             output_folder)
        if file_manager.all_audio:
            process_manager.audio_processing(data, output_folder)
        if file_manager.all_images:
            process_manager.image_processing(data, output_folder)


        asynchronous = data.get("asynchronous", False)

        if asynchronous:
            p = Process(target=process_manager.dispatcher.dispatch(data))
            p.start()
            json_str = json.dumps(response)
        else:
            results = process_manager.dispatcher.dispatch(data)
            json_str = json.dumps(results)

        return json_str


if __name__ == "__main__":
    coloredlogs.install(level='DEBUG', logger=logger)
    app.run()
