![VisionFlow](https://github.com/user-attachments/assets/b2cb7e79-3a1c-4246-8425-bb46bd7d61c7)

<img src="https://img.shields.io/badge/Python-3.12-blue" /> <img src="https://img.shields.io/badge/Streamlit-1.45-red" /> [![GPLv3 license](https://img.shields.io/badge/License-GPLv3-green.svg)](http://perso.crans.org/besson/LICENSE.html)

# VisionFlow

<img src="https://img.shields.io/badge/Version-0.1.0-blue" />

VisionFlow is a Streamlit-powered web application that allows you to generate images easily using the power of ComfyUI workflows. Simplify AI image creation with an intuitive and accessible interface.

![Capture d’écran de 2025-06-10 11-18-34](https://github.com/user-attachments/assets/d571fe14-1c8d-4c8b-81c4-0858f5d95459)

## Features

- Intuitive web interface built with Streamlit
- Integration with ComfyUI workflows
- AI-powered image generation
- Automatic ComfyUI startup (if not already running)
- Flexible parameter configuration
- Real-time result visualization

## Installation

### Prerequisites

- Python 3.12 or higher
- ComfyUI installed and configured

### Installation via GIT

If GIT is installed, open a terminal where you want to install VisionFlow and type:

```bash
git clone https://github.com/Franck-Demongin/VisionFlow.git
cd VisionFlow
```

### Manual Installation

If GIT is not installed, download the [ZIP](https://github.com/Franck-Demongin/VisionFlow/archive/refs/heads/main.zip) file, unzip it to your desired directory and rename it to VisionFlow.

### Environment Setup

Open a terminal in the VisionFlow folder.  
Create a virtual environment to isolate dependencies:

```bash
python -m venv .venv
```

_python_ should be replaced by the appropriate command according to your installation. On Linux, it could be _python3.12_, on Windows _python.exe_

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### ComfyUI

ComfyUI will be automatically launched by VisionFlow if it's not already running. You can also start ComfyUI manually if you want to access logs in a separate terminal (logs are not accessible when ComfyUI is launched by VisionFlow).

### Application Configuration

Create a `config.ini` file (copy and rename `config.ini.example`) or modify the existing configuration file.

The configuration file uses INI format with a `[comfyui]` section:

```ini
[comfyui]
    comfyui_path = /path/to/your/ComfyUI
    python_path = /path/to/your/ComfyUI/venv/bin/python
    url = localhost:8188
    ; uncoment the next ligne to add some parameters to start ComfyUI server
    ; params = --use-sage-attention
```

Available options include:

- `comfyui_path`: path to your ComfyUI installation directory
- `python_path`: path to Python executable in ComfyUI's virtual environment
- `url`: ComfyUI server address and port. Default: localhost:8188
- `params`: additional parameters for ComfyUI startup

To add uncommented parameters, separate them with a space. eg. `params = --use-sage-attention --auto-launch`

## Usage

### Starting the Application

To start VisionFlow, run:

```bash
streamlit run app.py
```

The application will be accessible at `http://localhost:8501`

### Generating Images

1. **Workflow Selection**: Choose your desired ComfyUI workflow
2. **Parameter Configuration**:
   - Seed: seed for random generation
   - Size: output image dimensions
   - Batch size: number of images to generate
3. **Prompt**: Enter your text description
4. **Generation**: Click the button to start generation

### Managing Results

- **Visualization**: Generated images display directly in the interface
- **Download**: Ability to download images individually
- **History**: Access to previous generations
- **Parameters**: View parameters used for each generation

## Supported Workflows

VisionFlow currently supports the following ComfyUI workflows:

- **Text-to-Image**: Generate images from text descriptions

_Coming soon:_

- Inpainting and outpainting
- Image-to-image transformation

## Adding Custom Workflows

VisionFlow allows you to integrate your own ComfyUI workflows. Here's how to add a new workflow:

**Prerequisites**

- Your workflow must be fully functional in ComfyUI
- All required nodes and models must be already installed
- Test your workflow in ComfyUI before integration

### Integration Steps

1. Export your workflow: In ComfyUI, go to Workflow > Export (API) to export your workflow as JSON
2. Copy workflow file: Place the exported JSON file in the workflows/ directory of your VisionFlow installation
3. Create configuration file: Create a configuration file with the same name but with \_config suffix

**Example:** workflowSDXL.json → workflowSDXL_config.json

### Configuration File Format

The configuration file must contain general information about the workflow and parameter mappings:

```json
{
  "name": "Display Name for UI",
  "description": "Brief description of what this workflow does",
  "global": {
    "seed": {
      "type": "int",
      "node": "25",
      "input": "noise_seed",
      "default": 42
    },
    "width": {
      "type": "int",
      "node": "144",
      "input": "value",
      "default": 1024
    },
    "height": {
      "type": "int",
      "node": "142",
      "input": "value",
      "default": 1024
    },
    "batch_size": {
      "type": "int",
      "node": "27",
      "input": "batch_size",
      "default": 1
    },
    "clip_l": {
      "type": "string",
      "node": "63",
      "input": "clip_l",
      "default": "{prompt}"
    },
    "t5xxl": {
      "type": "string",
      "node": "63",
      "input": "t5xxl",
      "default": "{prompt}"
    }
  }
}
```

#### Configuration Parameters

- name: Display name shown in VisionFlow UI
- description: Brief description of the workflow functionality
- global: Dictionary containing all workflow parameters

#### Required Parameters

All the parameters (name, description and global) are required.

The global section must include these standard parameters:

- seed: Random seed for generation
- width: Image width
- height: Image height
- batch_size: Number of images to generate

#### Parameter Structure

Each parameter contains:

- type: Variable type (int, float, string, etc.)
- node: Node ID as string (identifies the corresponding node in ComfyUI workflow)
- input: Field name in the ComfyUI workflow
- default: Default value for the parameter

#### Prompt Injection

For fields that should receive the user's prompt:

- The parameter name can be anything descriptive (eg. _prompt_, _clip_l_, _t5xxl_)
- Set default to "{prompt}"

Multiple fields can receive the same prompt by using "{prompt}" in their default values

This allows VisionFlow to automatically inject the user's text prompt into the appropriate nodes of your workflow.

## Troubleshooting

### ComfyUI Connection Issues

Check that:

- ComfyUI is started and accessible
- Connection parameters are correct in configuration
- No firewall is blocking the connection

### Performance Issues

- Reduce image size or batch size
- Check available system resources
- Ensure your GPU is properly configured

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Changelog

### v0.1.0 - 2025-06-10

**Added:**

- Intuitive Streamlit interface
- ComfyUI integration
- AI image generation
- Flexible configuration
- Custom workflow management

---

## Support

For help or to report issues, please open an issue on the GitHub repository.

**Built with ❤️ using Streamlit and ComfyUI**
