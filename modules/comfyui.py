import atexit
import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client) pip install websocket-client
import uuid
import json
import urllib.request, urllib.error
import urllib.parse
import subprocess
import os
import configparser

BASEDIR = os.path.dirname(os.path.abspath(__file__))

config_user = configparser.ConfigParser()
config_user.read(os.path.join(BASEDIR, os.pardir, "config.ini"))

config = {
    "comfyui": {
        "comfyui_path": config_user.get('comfyui', 'comfyui_path', fallback=""),
        "python_path": config_user.get('comfyui', 'python_path', fallback="venv/bin/python"),
        "url": config_user.get('comfyui', 'url', fallback="localhost:8188"),
        "params": config_user.get('comfyui', 'params', fallback="")
    }
}

client_id = str(uuid.uuid4())
    
def is_server_running() -> bool:
    """Vérifie si le serveur ComfyUI est actif"""
    try:
        r = urllib.request.urlopen("http://{}".format(config["comfyui"]["url"]))  # Timeout pour éviter les blocages
    except urllib.error.HTTPError as e:
        print(e.code)
        return False
    except urllib.error.URLError as e:
        print(e.reason)
        return False
    except:
        return False
    else:
        return True

def start_comfyui_server() -> subprocess.Popen:
    """Lance le serveur ComfyUI"""
    main_py_path = os.path.join(config["comfyui"]["comfyui_path"], "main.py")
    python_path = config["comfyui"]["python_path"]

    urls = config["comfyui"]["url"].split(":")
    host = urls[0]
    port = urls[1]
    
    cmd = [python_path, main_py_path, "--listen", host, "--port", port]

    # add params to cmd
    if config["comfyui"]["params"] != "":
        cmd.extend(config["comfyui"]["params"].split(" "))
    print(cmd)
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=config["comfyui"]["comfyui_path"],
        start_new_session=True
    )
    
    atexit.register(lambda: process.terminate())
    return process

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(config["comfyui"]["url"]), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(config["comfyui"]["url"], url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(config["comfyui"]["url"], prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            continue #previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images

def interrupt():
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(config["comfyui"]["url"], client_id))
    p = {"interrupt": True, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/interrupt".format(config["comfyui"]["url"]), data=data)
    urllib.request.urlopen(req)
    # free up resources
    p = {"unload_models": True, "free_memory": True, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/free".format(config["comfyui"]["url"]), data=data)
    urllib.request.urlopen(req)
    ws.close()
    
def main(config_wf: dict, workflow: dict, prompt_text: str, options: dict) -> tuple[list, str | None]:
    prompt = workflow

    print(options)

    wf_global = config_wf["global"]
    for k, v in wf_global.items():
        if v["default"] == "{prompt}":
            prompt[v["node"]]["inputs"][v["input"]] = prompt_text
            continue
        if k == "seed":
            prompt[v["node"]]["inputs"][v["input"]] = options["seed"]
            continue
        if k == "width":
            prompt[v["node"]]["inputs"][v["input"]] = options["width"]
            continue
        if k == "height":
            prompt[v["node"]]["inputs"][v["input"]] = options["height"]
            continue
        if k == "batch_size":
            prompt[v["node"]]["inputs"][v["input"]] = options["batch_size"]
            continue
        prompt[v["node"]]["inputs"][v["input"]] = v["default"]

    try:
        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(config["comfyui"]["url"], client_id))
        images = get_images(ws, prompt)
        # free up resources
        p = {"unload_models": True, "free_memory": True, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request("http://{}/free".format(config["comfyui"]["url"]), data=data)
        urllib.request.urlopen(req)
        ws.close()
    except ConnectionRefusedError as e:
        print(f"Error: Failed to connect to {config['comfyui']['url']}. Error: {e}")
        return [], f"""**Error:** Failed to connect to {config['comfyui']['url']}. Error: {e}.  
**Please start ComfyUI first.**"""

    images_list = []
    for node_id in images:
        for image_data in images[node_id]:
            images_list.append(image_data)
    
    return images_list, None

   
def comfyui(config_wf: dict, workflow: dict, prompt: str, options: dict) -> tuple[list, str | None]:
    images, error = main(config_wf=config_wf, workflow=workflow, prompt_text=prompt, options=options)
    return images, error
