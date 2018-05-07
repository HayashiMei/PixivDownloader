import os
import configparser

cur_path = os.path.dirname(os.path.realpath(__file__))

config_path = os.path.join(cur_path, 'config.ini')

conf = configparser.ConfigParser()
conf.read(config_path)

account = conf.get('auth', 'account')
password = conf.get('auth', 'password')