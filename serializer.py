class Serializer(object):
    def __init__(self):
        self.active_q_credentials = None
        self.input_folder = None
        self.output_folder = None
        self.file_type = None
        self.file_format = None
        self.mongodb = None

    def serialize(self, data):
        self.validate(data)

    def validate(self, data):
        """
        This Function can be used for validation of the data.
        Since then we parse the values and give them a default value if
        the key is not in the data.
        :param data: the json data of the request body
        :return:
        """
        self.input_folder = data.get('input_folder', "/shared")
        self.output_folder = data.get('output_folder', "/shared/outputs")

        self.file_type = data.get('file_type', "default")
        self.file_format = data.get('file_format', "default")
        self.active_q_credentials = data.get('brokerInfo', None)
