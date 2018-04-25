"""Supported File Format types"""
import os

videotypes = ['mp4', 'avi', 'wmv', '3gp', 'flv', 'mkv', 'mpg', 'mpeg', 'ogv',
              'ogg', 'mov', 'qt', 'ts', 'TOD', 'MOD', 'dv4', 'h264', 'vid',
              'ssf', 'sec']

imagetypes = ['jpeg', 'jpg', 'jif', 'jfif', 'png', 'pdf', 'tif', 'tiff', 'gif']

audiotypes = ['wav', 'mp3', 'aac', 'aiff', 'wma', 'flac']


class FileManager(object):
    def __init__(self):
        self.all_images = []
        self.all_videos = []
        self.all_audio = []

    def find_files(self, path_in, logger, type_of_file, f_format,
                   dir_v_path_out):
        self.logger = logger
        if (type_of_file in "default") and (f_format in "default"):
            self.all_videos = self.find_files_by_extension(path_in, videotypes)
            self.all_images = self.find_files_by_extension(path_in, imagetypes)
            self.all_audio = self.find_files_by_extension(path_in, audiotypes)

        elif type_of_file in ['Images', 'images']:
            self.all_images = self.find_files_by_extension(path_in,
                                                           imagetypes if f_format
                                                                         in "default" else f_format)
        elif type_of_file in ['Video', 'video']:
            self.all_videos = self.find_files_by_extension(path_in,
                                                           videotypes if f_format
                                                                         in "default" else f_format)
        elif type_of_file in ['Audio', 'audio']:
            self.all_audio = self.find_files_by_extension(path_in,
                                                          audiotypes if f_format in "default" else f_format)

        logger.info("Video: " + str(self.all_videos))
        logger.info("Images: " + str(self.all_images))
        logger.info("Audio: " + str(self.all_audio))

    def find_files_by_extension(self, path, extensions):
        self.logger.info('getting files from extensions')
        return [os.path.join(root, file) for root, dirs, files in os.walk(path) for
                file in files if
                file.split('.')[1] in extensions]