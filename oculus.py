from utils.configloader import configLoader
cl = configLoader() 
cl.read_yaml_to_env("config.yaml")