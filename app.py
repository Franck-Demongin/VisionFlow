import base64
from io import BytesIO
import math
import os
import json
import glob
import random
from time import perf_counter
import time
import streamlit as st
from PIL import Image

from modules.comfyui import comfyui, is_server_running, start_comfyui_server
from modules.comfyui import interrupt
from modules.config import VERSION

workflow_base_path = "./workflow/"

@st.cache_data
def list_workflows():
    workflows_path = glob.glob(os.path.join(workflow_base_path, "*_config.json"))
    workflows = []
    for config_path in workflows_path:
        # retrieve the file name
        file_name = os.path.basename(config_path)
        file_name = file_name.replace("_config.json", "")
        try:
            if os.path.isfile(os.path.join(workflow_base_path, f"{file_name}.json")):
                with open(config_path, "r") as f:
                    data = json.load(f)
                    workflows.append({"name": data["name"], "file": file_name, "description": data["description"]})
        except FileNotFoundError:
            pass

    return workflows

def get_workflow(workflow: str) -> tuple[dict, dict]:
    try:
        config_file = os.path.join(workflow_base_path, f"{workflow}_config.json")
        workflow_file= os.path.join(workflow_base_path, f"{workflow}.json")

        with open(config_file, "r") as file_config:
            config = json.load(file_config)
        with open(workflow_file, "r") as file_wf:
            wf = json.load(file_wf)

        return config, wf
    except FileNotFoundError:
        raise Exception(f"Workflow {workflow} not found")
    
@st.fragment
def button_download(data: str, name: str, key: str):
    st.download_button(label="Download", data =data, file_name=f"{name}.png", mime="image/png", key=key)

def button_reload(content: str, key: str):
    if st.button(":material/sync:", key=f"reload_{key}", type="tertiary", use_container_width=True, help="Reload the prompt"):
        st.session_state.reload_prompt = content
        time.sleep(5)

def button_edit(content: str, key: int):
    if st.button(":material/edit:", key=f"edit_{key}", type="tertiary", use_container_width=True, help="Edit the prompt"):
        st.session_state.edit_key = key

def display_question(content, level):
    if st.session_state.get("edit_key") == level:
        with st.chat_message("user"):
            with st.form(key=f"edit_form_{level}", border=False):
                st.text_area("Prompt", value=content, key=f"edit_prompt_{level}", label_visibility="collapsed", height=100)
                col1, col2, _ = st.columns([1, 1, 4])
                with col1:
                    if st.form_submit_button(":material/check: Edit", help="Edit", type="primary", use_container_width=True):
                        st.session_state.edit_key = None
                        st.session_state.reload_prompt = st.session_state.get(f"edit_prompt_{level}")
                        st.rerun()
                with col2:
                    if st.form_submit_button("Cancel", type="tertiary"):
                        st.session_state.edit_key = None
                        st.rerun()
    else:
        with st.chat_message("user"):
            st.markdown(content)
            _, col2, col3 = st.columns([19, 1, 1])
            with col2:
                button_reload(content=content, key=level)
            with col3:
                button_edit(content=content, key=level)

def display_response(content, options, level=0, error=None):
    with st.chat_message("assistant"):
        if error is not None:
            display_error(error)
        else:
            display_options(options)
            display_images(content, level)

def display_error(error):
    st.error(error, icon=":material/error:")

def display_images(content, level=0):
    col_1, col_2, col_3 = st.columns(3)

    for i, image in enumerate(content):
        pos = i % 3
        if pos == 0:
            with col_1:
                st.image(image, use_container_width=True)
                button_download(data=image, name=f"image_{level}_{i}", key=f"download_button_{level}_{i}")
        elif pos == 1:
            with col_2:
                st.image(image, use_container_width=True)
                button_download(data=image, name=f"image_{level}_{i}", key=f"download_button_{level}_{i}") 
        elif pos == 2:
            with col_3:
                st.image(image, use_container_width=True)
                button_download(data=image, name=f"image_{level}_{i}", key=f"download_button_{level}_{i}") 

def convert_second_to_time(seconds):
    m, s = divmod(seconds, 60)
    ms = s - math.floor(s)
    s = math.floor(s)
    h, m = divmod(m, 60)
    return f"{int(h):02d} h {int(m):02d} m {int(s):02d} s {int(ms*1000):03d} ms"

def display_options(options):
    with st.expander(f"Settings - Total time: {convert_second_to_time(options['elapsed'])}"):
        output = f"Workflow: {options['workflow']}  \nSeed: {options['seed']}  \nSize: {options['width']} x {options['height']}"
        st.write(output)

def format_size_item(item):
    w, h = item.split("x")
    symbole = "▫"
    if int(w) > int(h):
        symbole = "▭"
    if int(w) < int(h):
        symbole = "▯"
    return f"{symbole} {item}"

def save_history():
    pass

def use_last_seed():
    if st.session_state.last_seed is not None:
        st.session_state.seed = st.session_state.last_seed

@st.fragment
def display_sidebar_options():
    col1, col2 = st.columns([4,1], vertical_alignment="bottom")
    with col1:
        st.number_input("Seed", min_value=-1, max_value=2**32 - 1, help="Seed  \n-1: random seed", key="seed")
    with col2:
        st.button(":material/sync:", key="button_last_seed", type="primary", use_container_width=True, on_click=use_last_seed, help="Use last seed")
    
    st.selectbox(
        "Size", 
        ["1024x1024", "1152x896", "1216x832", "1344x768", "1536x640", "896x1152", "832x1216", "768x1344", "640x1536"], 
        format_func=format_size_item,
        help="Select an image size",
        key="size"
    )
    st.slider("Batch size", min_value=1, max_value=3, value=1, help="Number of images to generate", key="batch_size")

st.set_page_config(page_title="VisionFlow", page_icon=":material/palette:")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "wf_selected_path" not in st.session_state:
    st.session_state.wf_selected_path = None
if 'seed' not in st.session_state:
    st.session_state['seed'] = 42
if "last_seed" not in st.session_state:
    st.session_state.last_seed = None
if "reload_prompt" not in st.session_state:
    st.session_state.reload_prompt = None
if "edit_key" not in st.session_state:
    st.session_state.edit_key= None
if "running" not in st.session_state:
    st.session_state.running = False

server_running = False
if not is_server_running():
    print("Launching ComfyUI server...")
    process = start_comfyui_server()

    # Attente du démarrage avec timeout
    max_attempts = 24  # 2 minutes max (24 * 5s)
    attempts = 0

    # replace spinner by progress bar
    progress_text = "Waiting for server..."
    progress_bar = st.progress(0, text=progress_text)
    for i in range(max_attempts):
        if is_server_running():
            print("✓ Server ready!")
            server_running = True
            break

        print(f"Waiting for server... ({i + 1}/{max_attempts})")
        progress_bar.progress((i + 1) / max_attempts, text=progress_text)
        time.sleep(5)
        attempts += 1
    
    progress_bar.empty()

    if attempts >= max_attempts:
        st.error("⚠️ Timeout: server not started in time")
        print("⚠️ Timeout: server not started in time")
else:
    server_running = True

if server_running:
    with st.sidebar:
        wf_list = list_workflows()
        st.selectbox(
            "Workflow", 
            [wf["name"] for wf in wf_list], 
            index=None, 
            placeholder="Select a workflow", 
            help="Select a workflow to generate images",
            key="wf_choice"
        )

        if st.session_state.get("wf_choice"):
            description = [wf["description"] for wf in wf_list if wf["name"] == st.session_state.get("wf_choice")][0]
            st.session_state.wf_selected_path = [wf["file"] for wf in wf_list if wf["name"] == st.session_state.get("wf_choice")][0]
            st.write(description)
        else:
            st.session_state.wf_selected_path = None

        st.write("---")

        display_sidebar_options()
        
        st.write("---")

        placeholder = st.empty()
        with placeholder.container():
            if st.button(":material/cancel: CANCEL", key="button_interrupt", type="primary", use_container_width=True):
                interrupt()

        st.write("---")
        st.write(f"version {VERSION}")


    st.title(":material/palette: VisionFlow")
    st.subheader("The easy way to generate images with ComfyUI", divider=True)
    st.write("Tired of complexity? VisionFlow simplifies the power of ComfyUI into an intuitive interface. Create stunning visuals, explore new ideas, and master generative AI effortlessly. Start bringing your visions to life today!")

    for index, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            display_question(content=message["content"], level=index)
        if message["role"] == "assistant":
            display_response(content=message["content"], options=message["options"], level=index, error=message.get("error"))

    if st.session_state.get("wf_selected_path") is None:
        st.warning("Please select a workflow to start generate images.")

    if prompt:=(st.chat_input("Prompt", key="prompt", disabled=st.session_state.get("wf_selected_path") is None) or st.session_state.get("reload_prompt")):

        st.session_state.running = True

        st.session_state.reload_prompt = None
        
        w, h = st.session_state.get("size", "1024x1024").split("x")
        st.session_state.last_seed = st.session_state.get("seed") if st.session_state.get("seed") != -1 else random.randint(0, 2**32 - 1)

        options = {
            "seed": st.session_state.get("last_seed"),
            "width": int(w), 
            "height": int(h), 
            "batch_size": st.session_state.get("batch_size")
        }
            
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_question(content=prompt, level=len(st.session_state.messages))

        config, workflow = get_workflow(workflow=st.session_state.get('wf_selected_path', "munchaku_creaart_ultimate.json"))
        
        with st.spinner("Generating images..."):
            start = perf_counter()
            images, error = comfyui(config_wf=config, workflow=workflow, prompt=prompt, options=options)
            
            elapsed = perf_counter() - start

            st.session_state.running = False
            
            options = {"workflow": st.session_state.get("wf_choice"), "elapsed": elapsed} | options
            
            st.session_state.messages.append({"role": "assistant", "content": images, "options": options, "error": error})
            display_response(content=images, options=options, level=len(st.session_state.messages), error=error)

            save_history()


