'''
Check if the versions of Streamlit and Ollama are compatible
'''

import subprocess
from modules.config import OLLAMA_MIN, STREAMLIT_MIN

# create an Exception class
class VersionError(Exception):
    pass

def check_versions() -> tuple[str, str]:
    ollama_version = get_ollama_version()
    streamlit_version = get_streamlit_version()

    try:
        errors = []
        if ollama_version < OLLAMA_MIN:
            errors.append({
                    "lib": "ollama", 
                    "error": f"Ollama version {ollama_version} is too old. Minimum version is {OLLAMA_MIN}"
            })
        if streamlit_version < STREAMLIT_MIN:
            errors.append({
                    "lib": "streamlit", 
                    "error": f"Streamlit version {streamlit_version} is too old. Minimum version is {STREAMLIT_MIN}"
            })

        if errors:
            error_msg = "\n".join([error['error'] for error in errors])
            error_msg += "\n------\nPlease update " + " and ".join([error['lib'] for error in errors])
            raise VersionError(error_msg)

    except VersionError as e:
        print(e)
        exit(1)


    return ollama_version, streamlit_version


def get_ollama_version() -> str:
    """
    Get the version number of Ollama.

    Returns:
        str: The version number of Ollama.
    """
    version = subprocess.check_output(['ollama', '--version']).decode('utf-8')
    return version.strip().split(' ')[-1]

def get_streamlit_version() -> str:
    """
    Get the version number of Streamlit.

    Returns:
        str: The version number of Streamlit.
    """
    return __import__('streamlit').__version__