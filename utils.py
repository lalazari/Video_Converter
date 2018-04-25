import errno
import logging
import os

logger = logging.getLogger('web')


def mkdir_p(path):
    """
     this function do what mkdir -p does on unix systems
    :param path: a string path
    :return: None
    """
    try:
        logger.info("mkdir_p: Creating path {}".format(path))
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise