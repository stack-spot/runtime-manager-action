import inspect
import os
import time
import requests
import json
from pprint import pprint
from pathlib import Path
from ruamel.yaml import YAML
from io import StringIO


class Inputs:
    def __init__(self):
        self.action_path = os.getenv("ACTION_PATH")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_key = os.getenv("CLIENT_KEY")
        self.client_realm = os.getenv("CLIENT_REALM")
        self.tf_state_bucket_name = os.getenv("TF_STATE_BUCKET_NAME")
        self.tf_state_region = os.getenv("TF_STATE_REGION")
        self.iac_bucket_name = os.getenv("IAC_BUCKET_NAME")
        self.iac_region = os.getenv("IAC_REGION")
        self.verbose: bool = os.getenv("VERBOSE") is not None
        self.validate()

    def validate(self):
        """
        validate method is a part of a class and is used to validate the instance variables of the class.
        It checks whether all the instance variables (attributes) of the class are set or not.
        :return:
        """
        has_errors = False
        for [name, value] in inspect.getmembers(self):
            if not name.startswith('_') and not inspect.ismethod(value) and value is None:
                print(f"- {name} is not set.")
                has_errors = True

        if has_errors:
            print("- Some mandatory input is empty. Please, check the input list.")
            exit(1)


def yaml() -> YAML:
    """
     Loads the YAML object with the desired configurations alike stackspot's CLI does
     to avoid any compatibility issues.
    """
    yml = YAML()
    yml.indent(mapping=2, sequence=4, offset=2)
    yml.allow_unicode = True
    yml.default_flow_style = False
    yml.preserve_quotes = True
    return yml


def safe_load(content: str) -> dict:
    """
        Load the YAML content and return the dictionary with its content.
        :param content: YAML String to load as Dict
        :return:
    """
    yml = yaml()
    return yml.load(StringIO(content))


def save_output(name: str, value: str):
    """
        Save the output in the Github Actions output file.
        :param name: Name of the output
        :param value: Value of the output
    """
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
        print(f'{name}={value}', file=output_file)


def load_manifesto(action_path: str, verbose: bool) -> dict:
    """
        Load the manifesto file and return the dictionary with its content.
        :param action_path: Path to the Github action folder
        :param verbose: Verbose flag to print the manifesto content
    """
    with open(Path(action_path + '/manifest.yaml'), 'r') as file:
        manifesto_yaml = file.read()

    manifesto_dict = safe_load(manifesto_yaml)
    if verbose:
        print("- MANIFESTO:", manifesto_dict)

    manifestoType = manifesto_dict["manifesto"]["kind"]
    appOrInfraId = manifesto_dict["manifesto"]["spec"]["id"]

    if manifestoType not in ['application', 'shared-infrastructure']:
        print("- MANIFESTO TYPE not recognized. Please, check the input.")
        exit(1)

    print(f"{manifestoType} project identified, with ID: {appOrInfraId}")
    return manifesto_dict


def load_env_vars() -> Inputs:
    """
        Load the environment variables and return the Inputs object with its content.
        :return: Inputs object with the content of the environment variables
    """
    return Inputs()


def retrieve_token(client_id: str, client_key: str, client_realm: str) -> str:
    """
        Authenticate on StackSpot's IAM Service and retrieve the access token
        :param client_id: Client ID to authenticate
        :param client_key: Client Key to authenticate
        :param client_realm: Client Realm to authenticate
        :return: Access Token to be used on the API requests
    """

    iam_url = f"https://auth.stackspot.com/{client_realm}/oidc/oauth/token"
    iam_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    iam_data = {"client_id": client_id, "grant_type": "client_credentials", "client_secret": client_key}

    print("Authenticating...")
    login_requests = requests.post(
        url=iam_url,
        headers=iam_headers,
        data=iam_data
    )

    if login_requests.status_code != 200:
        print("- Error during IAM authentication")
        print("- Status:", login_requests.status_code)
        print("- Error:", login_requests.reason)
        print("- Response:", login_requests.text)
        exit(1)

    print("Successfully authenticated!")

    response = login_requests.json()

    if "access_token" not in response:
        print("- Access token not found in the response.")
        print("- Response:", response)
        print("- Please reach out to StackSpot's support team.")
        exit(1)

    return response["access_token"]


def validate_manifesto(manifesto_dict: dict):
    """
    Validate the manifesto dictionary and check if the mandatory fields are present.
    :param manifesto_dict:
    """
    manifesto_value = manifesto_dict["manifesto"]
    if manifesto_value is None:
        print("- MANIFESTO not informed or couldn't be extracted.")
        exit(1)

    version_tag = manifesto_dict["versionTag"]
    if version_tag is None:
        print("- Version Tag not informed or couldn't be extracted.")
        exit(1)

    is_api = manifesto_dict["isApi"]
    if is_api is None:
        print("- API TYPE not informed or couldn't be extracted.")
        exit(1)

    envId = manifesto_dict["envId"]
    if envId is None:
        print("- ENVIRONMENT ID not informed or couldn't be extracted.")
        exit(1)

    wksId = manifesto_dict["workspaceId"]
    if wksId is None:
        print("- WORKSPACE ID not informed or couldn't be extracted.")
        exit(1)

    manifesto_type = manifesto_dict["manifesto"]["kind"]

    if manifesto_type not in ['application', 'shared-infrastructure']:
        print("- MANIFESTO TYPE not recognized. Please, check the input.")
        exit(1)


def deploy_self_hosted(manifesto_dict: dict, access_token: str, inputs: Inputs):
    request_data = build_deploy_request_body(manifesto_dict, inputs)

    deploy_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    print("Deploying Self-Hosted...")

    manifestoType = manifesto_dict["manifesto"]["kind"]

    deploy_type = 'app' if manifestoType == 'application' else 'infra'

    self_hosted_deploy_infra_url = f"https://runtime-manager.v1.stackspot.com/v2/run/self-hosted/deploy/${deploy_type}"
    request_deploy = requests.post(
        url=self_hosted_deploy_infra_url,
        headers=deploy_headers,
        data=request_data
    )

    if request_deploy.status_code != 201:
        print("- Error starting self hosted deploy run")
        print("- Status:", request_deploy.status_code)
        print("- Error:", request_deploy.reason)
        print("- Response:", request_deploy.text)
        exit(1)

    deploy_response = request_deploy.json()
    runId = deploy_response["runId"]
    runType = deploy_response["runType"]
    tasks = deploy_response["tasks"]

    save_output('tasks', tasks)
    save_output('run_id', runId)

    print(f"- RUN {runType} successfully created with ID: {runId}")
    pprint(f"- RUN TASKS LIST: ")
    pprint(tasks)

    return runId


def build_deploy_request_body(manifesto_dict: dict, inputs: Inputs):
    """
    Build the request body to deploy the self-hosted infrastructure
    :param manifesto_dict:
    :param inputs:
    :return request_data:
    """
    branch = None
    if "runConfig" in manifesto_dict:
        if "checkoutBranch" in manifesto_dict["runConfig"]:
            branch = manifesto_dict["runConfig"]["checkoutBranch"]
            print("Branch informed:", branch)

    api_contract_path = None
    if "apiContractPath" in manifesto_dict:
        api_contract_path = manifesto_dict["apiContractPath"]
        print("API contract path informed:", api_contract_path)

    request_data = json.dumps(manifesto_dict)
    config_data = json.dumps(
        {
            "config": {
                "tfstate": {
                    "bucket": inputs.tf_state_bucket_name,
                    "region": inputs.tf_state_region
                },
                "iac": {
                    "bucket": inputs.iac_bucket_name,
                    "region": inputs.iac_region
                }
            }
        }
    )

    request_data = json.loads(request_data)
    request_data = {**request_data, **json.loads(config_data)}

    if branch is not None:
        branch_data = json.dumps(
            {
                "runConfig": {
                    "branch": branch
                }
            }
        )
        request_data = {**request_data, **json.loads(branch_data)}
    if api_contract_path is not None:
        api_data = json.dumps(
            {
                "apiContractPath": api_contract_path
            }
        )
        request_data = {**request_data, **json.loads(api_data)}
    request_data = json.dumps(request_data)

    if inputs.verbose is not None:
        print("- DEPLOY RUN REQUEST DATA:", request_data)
    return request_data


def await_validation(run_id: str, access_token: str, inputs: Inputs):
    """
    Await the validation of the deployment request until not in PROCESSING_REQUEST status
    :param run_id:
    :param access_token:
    :param inputs:
    :return:
    """
    print("We are now going to validate the deployment request on the background")
    print("Please, wait a few seconds...")
    print("Awaiting validation...")
    validation_url = f"https://runtime-manager.v1.stackspot.com/v2/run/run-status/{run_id}"
    validation_headers = {"Authorization": f"Bearer {access_token}"}

    forbidden_retry = 0

    while True:
        validation_request = requests.get(
            url=validation_url,
            headers=validation_headers
        )

        if validation_request.status_code == 403:
            forbidden_retry += 1
            if forbidden_retry > 3:
                print("Forbidden error after 3 retries. Exiting...")
                exit(1)
            print("Forbidden error. Refreshing token...")
            new_token = retrieve_token(inputs.client_id, inputs.client_key, inputs.client_realm)
            validation_headers = {"Authorization": f"Bearer {new_token}"}
            continue

        if validation_request.status_code != 200:
            print("- Error getting validation status")
            print("- Status:", validation_request.status_code)
            print("- Error:", validation_request.reason)
            print("- Response:", validation_request.text)
            exit(1)

        response = validation_request.json()
        run_status = response["status"]

        if run_status == "PROCESSING_REQUEST":
            time.sleep(5)
            print("...")
            continue

        elif run_status == "RUNNING":
            print("Validation is completed successfully")
            print("We will continue your deploy process")
            break

        else:
            print("There were some problems with deployment request")
            for task in response["tasks"]:
                if "errorMessage" in task and task["errorMessage"] is not None:
                    print(f"Task {task['id']} failed with error: {task['errorMessage']}")


if __name__ == "__main__":
    user_inputs = load_env_vars()
    manifesto = load_manifesto(user_inputs.action_path, user_inputs.verbose)
    validate_manifesto(manifesto)
    token = retrieve_token(user_inputs.client_id, user_inputs.client_key, user_inputs.client_realm)
    run_id_received = deploy_self_hosted(manifesto, token, user_inputs)
    await_validation(run_id_received, token, user_inputs)
