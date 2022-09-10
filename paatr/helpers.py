import os
import tempfile
import zipfile
import yaml

from fastapi import Request
from fastapi.responses import JSONResponse

from . import (APP_CONFIG_FILE, CONFIG_KEYS_X, CONFIG_KEYS, 
                CONFIG_VALUE_VALIDATOR, DOCKER_TEMPLATE)

async def handle_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

async def save_file(filename, dir_path, contents, _mode="wb"):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    try:
        with open(os.path.join(dir_path, filename), _mode) as fp:
            fp.write(contents)
    except Exception as e:
        return False
    
    return True

async def get_app_config(config_path):
    with open(config_path, "r") as fp:
        config = yaml.safe_load(fp)
    
    if not config:
        return False, f"Invalid {APP_CONFIG_FILE} file"
    
    for key in CONFIG_KEYS_X:
        if key not in config:
            return False, f"Missing {key} key in {APP_CONFIG_FILE}"

        if not CONFIG_VALUE_VALIDATOR[key](config[key]):
            return False, f"Invalid value for {key} key in {APP_CONFIG_FILE}"

    for k,v in config.items():
        if k not in CONFIG_KEYS:
            return False, f"Invalid key {k} in {APP_CONFIG_FILE}"
        
        if k in CONFIG_KEYS_X:
            if not v:
                return False, f"Invalid value for {k} in {APP_CONFIG_FILE}"

    return True, config

def generate_docker_config(config):
    run = config.pop("run")
    if type(run) == list:
        run = " && ".join(run)

    return DOCKER_TEMPLATE.format(**config, run=f"RUN {run}")

async def build_app(app_path):
    if not os.path.exists(app_path):
        return "No files found for this app"
    
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(app_path, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)

                files = os.listdir(tmp_dir)
                
                if APP_CONFIG_FILE not in files:
                    return f"No {APP_CONFIG_FILE} file found in the app files"

                (is_valid, config) = await get_app_config(os.path.join(tmp_dir, APP_CONFIG_FILE))

                if not is_valid:
                    return config
                
                dockerfile = generate_docker_config(config)

                with open(os.path.join(tmp_dir, "dockerfile"), "w") as fp:
                    fp.write(dockerfile)
                
    except Exception as e:
        return "Failed to build app"
    
    return "App built successfully"