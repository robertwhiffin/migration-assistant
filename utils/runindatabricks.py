from utils.configloader import ConfigLoader
from dbtunnel import dbtunnel
def run_app():
    #load config file into environment variables
    cl = ConfigLoader()
    cl.read_yaml_to_env("config.yaml")


    #dbtunnel.kill_port(8080)
    app='././gradio_app.py'
    dbtunnel.gradio(path=app).run()