import os
from datetime import datetime
import tempfile
import yaml

from docker.errors import ImageNotFound, NotFound, BuildError
from fastapi import Request
from fastapi.responses import JSONResponse
from git import Repo

from . import (APP_CONFIG_FILE, CONFIG_KEYS_X, CONFIG_KEYS, 
                CONFIG_VALUE_VALIDATOR, DOCKER_TEMPLATE, DOCKER_CLIENT, 
                BUILD_LOGS_TABLE)

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

def get_app_config(config_path):
    """
    Creates a config dict from the app `paatr.yaml` config file

    Args:
        config_path (str): Path to the app `paatr.yaml` config file
    
    Returns:
        (bool, dict): Tuple of (success, config)
    """

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

    return DOCKER_TEMPLATE.format(**config, run=f"RUN {run}", app_name=config["name"])


def _add_build_log(build_id, app_id, log, state="building"):
    with BUILD_LOGS_TABLE as logs_db:
        app_data = logs_db.get(app_id, dict())
        build_data = app_data.get(build_id, dict())
        app_logs = build_data.get("logs", [])
        app_logs.append(log)

        if "created_at" not in build_data:
            build_data["created_at"] = datetime.utcnow().isoformat()
            
        BUILD_LOGS_TABLE[app_id] = {
            **app_data,
            build_id: {
                **build_data,
                "logs": app_logs,
                "status": state,
                "build_id": build_id
            }
        }

def build_app(build_id, git_url, app_name, app_id):
    """
    Builds an app from a git repository and generates 
    a docker config file from the app `paatr.yaml` config file

    Args:
        git_url (str): URL of the git repository
        app_name (str): Name of the app
    
    Returns:
        str: Build message
    """

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            app_dir = os.path.join(tmp_dir, app_name)
            repo = Repo.clone_from(url=git_url, to_path=app_dir)

            files = os.listdir(app_dir)
            if APP_CONFIG_FILE not in files:
                _add_build_log(build_id, app_id, f"Missing {APP_CONFIG_FILE} file", "failed")
                return

            (is_valid, config) = get_app_config(os.path.join(app_dir, APP_CONFIG_FILE))

            if not is_valid:
                _add_build_log(build_id, app_id, config, "failed")
                return
            else:
                _add_build_log(build_id, app_id, "Successfully parsed config file")

            config["name"] = app_name
            dockerfile = generate_docker_config(config)

            with open(os.path.join(tmp_dir, "dockerfile"), "w") as fp:
                fp.write(dockerfile)

            image, _ = build_docker_image(build_id, tmp_dir, app_name, app_id)

        _add_build_log(build_id, app_id, "Successfully built image", "success")
        return 

    except BuildError as e:
        for line in e.build_log:
            if 'stream' in line:
                _add_build_log(build_id, app_id, line['stream'].strip(), "failed")
    
    _add_build_log(build_id, app_id, "Failed to build image", "failed")
    return "Failed to build app"

###################################################################
# Docker related functions                                       #
###################################################################

def build_docker_image(build_id, app_dir, app_name, app_id=""):
    """
    Build docker image from app directory

    Args:
        app_dir (str): Path to app directory
        app_name (str): Name of the app
    
    Returns:
        (docker.models.images.Image, str): Docker image object and build logs
    """
    image, logs = DOCKER_CLIENT.images.build(path=app_dir, tag=app_name, rm=True)

    for line in logs:
        if "stream" in line:
            line_str = line["stream"].strip()
            if line_str.startswith("Step ") or line_str.startswith("--->"):
                continue
            if line_str.strip():
                _add_build_log(build_id, app_id, line_str)
    
    return image, logs

def get_app_status(app_name):
    """
    Get status of container with app_name

    Args:
        app_name (str): Name of the app
    
    Returns:
        dict: Status of the app
    """

    if not get_image(app_name):
        return {"message": "App has not been built", "status": "not-built"}

    container = get_container(app_name)
    if container:
        if container.status == "running":
             return {"message": "App is running", "status": "running"}

    return {"message": "App is not running", "status": "not-running"}

def get_image(app_name):
    try:
        return DOCKER_CLIENT.images.get(app_name)
    except ImageNotFound:
        return None

def get_container(app_name):
    try:
        return DOCKER_CLIENT.containers.get(app_name)
    except NotFound:
        return None

async def stop_container(app_name):
    if cont := get_container(app_name):
        cont.stop()

def remove_container(app_name):
    if cont := get_container(app_name):
        cont.remove(force=True)

async def run_docker_image(app_name, app_id_digit):
    """
    Runs docker image with app_name

    Args:
        app_name (str): Name of the app
        app_id_digit (int): Digit to be used to generate a unique port for the app
    """

    if not get_image(app_name):
        return "App not found"
        
    await stop_container(app_name)

    if cont := get_container(app_name):
        cont.start()
    else:
        (DOCKER_CLIENT.containers
                    .run(app_name, ports={'5000/tcp': 10000 + app_id_digit}, 
                            detach=True, name=app_name))