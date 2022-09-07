import os
import logging
from datetime import datetime
import json
import sys
import argparse
from typing import List

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_ROOT = os.path.join(PROJECT_ROOT, 'logs')


def configure_logger(logger, log_level=logging.DEBUG, filepath=None, filename=None, log_root=LOG_ROOT):
    """
    Configures a logger for the given parameters. The logger always outputs to the default console, and logs to file
    if a filename is specified. The filename is prefixed with a date stamp, the current days file is appended new log
    messages. The file will be located at 'logs' directory in the project root. A subdirectory can be specified.
    It is ignored if no filename is given. The default log level is DEBUG.
    :param logger: The logger instance to configure
    :param log_level: The log level to output
    :param filepath: The subdirectory in the 'logs' directory.
    :param filename: The filename to log to
    :return: The configured logger instance
    """
    # default level for logger, overwrite for handler
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s:  %(message)s')

    # output to file if filename specified
    # if filename:
    #     log_path = log_root
    #     if filepath:
    #         log_path = os.path.join(LOG_ROOT, filepath)
    #     if not os.path.exists(log_path):
    #         os.makedirs(log_path)
    #     timestamp = datetime.now().strftime('%Y-%m-%d')
    #     log_file = os.path.join(log_path, f'{timestamp}_{filename}.log')
    #     fh = logging.FileHandler(log_file)
    #     fh.setLevel(log_level)
    #     fh.setFormatter(formatter)
    #     logger.addHandler(fh)

    # always output to console
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def dump_json(dictionary, filepath, filename, indent=2, timestamp=True):
    json_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(json_path):
        os.makedirs(json_path)
    f = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}-{filename}.json' if timestamp else f'{filename}.json'
    path = os.path.join(json_path, f)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dictionary, f, indent=indent)
    return path


def load_json(filepath):
    json_path = os.path.join(PROJECT_ROOT, filepath)
    with open(json_path, 'r') as f:
        return json.load(f)


def print_update(message):
    message = ('\r' + message)
    sys.stdout.write(message)
    sys.stdout.flush()


def add_db_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('--db_host', default='localhost', help='The hostname or IP of the database')
    parser.add_argument('--db_port', default='5432', help='The port the database host')
    parser.add_argument('--db_user', default='tcb', help='The username to connect with the database')
    parser.add_argument('--db_password', default='tcb', help='The password to connect with the databse')
    parser.add_argument('--db_name', default='tcb', help='The name of the database')
    parser.add_argument('--db_schema', required=True, help='The schema name')
    parser.add_argument('--db_type', type=str, default='postgresql', help='The type when using SQLAlchemy to connect')
    parser.add_argument('--db_driver', type=str, default=None, help='The driver when using SQLAlchemy to connect')


def str2bool(v: str) -> bool:
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
