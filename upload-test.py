import os
import gradio as gr

def read_sql(path):
    with open(path.name) as fd:
        sql_code = fd.read()
    return(sql_code)

def upload_file(files):
    file_paths = [file.name for file in files]
    return file_paths

with gr.Blocks() as demo:
    file_output = gr.File()
    upload_button = gr.UploadButton("Click to Upload a File", file_types=["image", "video"], file_count="multiple")
    upload_button.upload(upload_file, upload_button, file_output)

demo.launch()

# with gr.Blocks() as demo:
#     upload_button = gr.UploadButton("Click to Upload a File", file_types=['.sql'], file_count="single")
#     uploaded_code = gr.Code(value = "")
#     upload_button.upload(read_sql, upload_button, uploaded_code)

# #demo.launch(share = True)
demo.queue().launch(
    server_name=os.getenv("GRADIO_SERVER_NAME"), 
    server_port=int(os.getenv("GRADIO_SERVER_PORT"))
  )