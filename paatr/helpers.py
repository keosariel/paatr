import os
from datetime import datetime
import re
import tempfile
import yaml

from docker.errors import ImageNotFound, NotFound, BuildError
from fastapi import Request
from fastapi.responses import JSONResponse
from git import Repo
from nginxparser_eb import dumps as nginx_dumps
from nginxparser_eb import load as nginx_load
from nginxparser_eb import UnspacedList

from . import (APP_CONFIG_FILE, CONFIG_KEYS_X, CONFIG_KEYS, 
                CONFIG_VALUE_VALIDATOR, DOCKER_TEMPLATE, DOCKER_CLIENT, 
                BUILD_LOGS_TABLE, INSTALLATION_FILE, DEFAULT_PORT, PYTHON_RUNTIMES, Config)

APP_NAME_REGEX = re.compile(r"^[a-zA-Z]([a-zA-Z0-9_-]{3,20})$")

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
        return False, f"Invalid `{APP_CONFIG_FILE}` file"
    
    for key in CONFIG_KEYS_X:
        if key not in config:
            return False, f"Missing `{key}` key in {APP_CONFIG_FILE}"

        if not CONFIG_VALUE_VALIDATOR[key](config[key]):
            return False, f"Invalid value for `{key}` key in {APP_CONFIG_FILE}"

    for k,v in config.items():
        if k not in CONFIG_KEYS:
            return False, f"Invalid key `{k}` in {APP_CONFIG_FILE}"
        
        if k in CONFIG_KEYS_X:
            if not v:
                return False, f"Invalid value for `{k}` in {APP_CONFIG_FILE}"

    if config["runtime"] not in PYTHON_RUNTIMES:
        return False, f"Unknown runtime `{config['runtime']}`"

    config["runtime"] = PYTHON_RUNTIMES[config["runtime"]]
    config["port"] = DEFAULT_PORT
    return True, config

def generate_docker_config(config):
    run = config.pop("run")
    if type(run) == list:
        run = " && ".join(run)

    return DOCKER_TEMPLATE.format(**config, run=f"RUN {run}", app_name=config["name"])


def _add_build_log(build_id, app_id, log, state="building", log_type="build"):
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
                "build_id": build_id,
                "type": log_type
            }
        }

def build_app(build_id, git_url, app_name, app_id, repo_url):
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
            _add_build_log(build_id, app_id, f"Cloning {repo_url} ")
            try:
                repo = Repo.clone_from(url=git_url, to_path=app_dir)
            except Exception as e:
                _add_build_log(build_id, app_id, f"Error cloning {repo_url}", "failed")
                return f"Error cloning {repo_url}"

            files = os.listdir(app_dir)
            if APP_CONFIG_FILE not in files:
                _add_build_log(build_id, app_id, f"Missing {APP_CONFIG_FILE} file", "failed")
                return "Missing paatr.yaml file"

            (is_valid, config) = get_app_config(os.path.join(app_dir, APP_CONFIG_FILE))

            if not is_valid:
                _add_build_log(build_id, app_id, config, "failed")
                return
            else:
                _add_build_log(build_id, app_id, "Successfully parsed config file")

            if INSTALLATION_FILE in files:
                _add_build_log(build_id, app_id, f"Adding installation file `{INSTALLATION_FILE}`")
                config["run"] = [f"pip install -r {INSTALLATION_FILE}"]
                _add_build_log(build_id, app_id, "Successfully added installation file")

            config["name"] = app_name
            dockerfile = generate_docker_config(config)

            with open(os.path.join(tmp_dir, "dockerfile"), "w") as fp:
                fp.write(dockerfile)

            _add_build_log(build_id, app_id, "Installing dependencies...")
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
# Docker related functions                                        #
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

def stop_container(app_name):
    if cont := get_container(app_name):
        cont.stop()

def remove_container(app_name):
    if cont := get_container(app_name):
        cont.remove(force=True)

def run_docker_image(app_data, run_id):
    """
    Runs docker image with app_name

    Args:
        app_name (str): Name of the app
        app_id_digit (int): Digit to be used to generate a unique port for the app
        run_id (str): Unique ID for the run
    """
    app_name = app_data.name
    app_id_digit = app_data.id
    app_id = app_data.app_id

    _add_subdomain(app_data)

    if not get_image(app_name):
        _add_build_log(run_id, app_id, "App not found", "failed", log_type="run")
        return "App not found"
    
    try:
        stop_container(app_name)

        if cont := get_container(app_name):
            _add_build_log(run_id, app_id, "Restarting container", "setting-up", log_type="run")
            cont.start()
        else:
            _add_build_log(run_id, app_id, "Building container", "setting-up", log_type="run")
            app_dir = os.path.join(Config.APP_FILES_DIR, app_name)

            if not os.path.exists(app_dir):
                os.mkdir(app_dir)
            _add_build_log(run_id, app_id, "Setting up logs", "setting-up", log_type="run")
            container = (DOCKER_CLIENT.containers
                        .run(app_name, ports={f'{DEFAULT_PORT}/tcp': 10000 + app_id_digit}, 
                                detach=True, name=app_name, volumes={app_dir: {'bind': '/paatr', 'mode': 'rw'}}))
            
        _add_build_log(run_id, app_id, "Successfully ran container", "success", log_type="run")
    except Exception as e:
        _add_build_log(run_id, app_id, "Failed to run container", "failed", log_type="run")
        return "Failed to run app"

def container_logs(app_name):
    if cont := get_container(app_name):
        if not cont:
            return None
    
    app_dir = os.path.join(Config.APP_FILES_DIR, app_name)
    app_logs = os.path.join(app_dir, "logs.txt")

    if os.path.exists(app_logs):
        tail_lines = tail(open(app_logs, 'r'), 100)
        return tail_lines

    return None

def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end
    
    Args:
        f (file): File object
        lines (int, optional): Number of lines to return. Defaults to 1.
        _buffer (int, optional): Buffer size. Defaults to 4098.
    
    Returns:
        str: Last X lines of the file
    
    Resource: https://stackoverflow.com/a/13790289/10527467
    """
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        # Removed this line because it was redundant the while will catch
        # it, I left it for history
        # if len(lines_found) > lines:
        #    break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1
    return lines_found[-lines:]



###################################################################
# Nginx related functions                                         #
###################################################################


def _subdomain_exists(subdomain):
    try:
        payload = nginx_load(open(Config.NGINX_ENABLED_PAATR_APPS))
    except Exception as e:
        # TODO: Log error
        return False

    for directive in payload:
        directive_name, directive_value = directive

        if directive_name[0] == "server":
            for subdirective in directive_value:
                subdirective_name, subdirective_value = subdirective

                if subdirective_name == "server_name":
                    if type(subdirective_value) == str:
                        if subdirective_value.strip().startswith(subdomain+"."):
                            return True

    return False

def _add_subdomain(app_data):
    """
    Add subdomain to app

    Args:
        app_data (App): App object
    """
    app_name = app_data.name.lower().strip()

    if not _subdomain_exists(app_name):
        if not APP_NAME_REGEX.fullmatch(app_name):
            return "Invalid app name"

        config = f"""
server {{
    listen 80;
    server_name {app_name}.paatrapp.live;

    location / {{
        proxy_pass http://localhost:{10000 + app_data.id};
    }}
}}
        """

        with open(Config.NGINX_ENABLED_PAATR_APPS, "a") as f:
            f.write(config)
        
        if Config.MODE == "prod":
            os.system("sudo systemctl restart nginx")