import os
import requests
import json
from pathlib import Path
from ruamel.yaml import YAML
from io import StringIO


def yaml() -> YAML:
    yml = YAML()
    yml.indent(mapping=2, sequence=4, offset=2)
    yml.allow_unicode = True
    yml.default_flow_style = False
    yml.preserve_quotes = True
    return yml


def safe_load(content: str) -> dict:
    yml = yaml()
    return yml.load(StringIO(content))


def save_output(name: str, value: str):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
        print(f'{name}={value}', file=output_file)


def build_pipeline_url() -> str:
    GITHUB_SERVER_URL = os.getenv("GITHUB_SERVER_URL")
    GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
    GITHUB_RUN_ID = os.getenv("GITHUB_RUN_ID")
    if None in [GITHUB_SERVER_URL, GITHUB_REPOSITORY, GITHUB_RUN_ID]:
        print("- Some mandatory GitHub Action environment variable is empty.")
        exit(1)
    url = f"{GITHUB_SERVER_URL}/{GITHUB_REPOSITORY}/actions/runs/{GITHUB_RUN_ID}"
    return url

STACKSPOT_IAM_URL = os.getenv("STACKSPOT_IAM_URL")
STACKSPOT_RUNTIME_MANAGER_URL = os.getenv("STACKSPOT_RUNTIME_MANAGER_URL")
ACTION_PATH = os.getenv("ACTION_PATH")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_KEY = os.getenv("CLIENT_KEY")
CLIENT_REALM = os.getenv("CLIENT_REALM")
TF_STATE_BUCKET_NAME = os.getenv("TF_STATE_BUCKET_NAME")
TF_STATE_REGION = os.getenv("TF_STATE_REGION")
IAC_BUCKET_NAME = os.getenv("IAC_BUCKET_NAME")
IAC_REGION = os.getenv("IAC_REGION")
VERBOSE = os.getenv("VERBOSE")
SKIP_DEPLOY = os.getenv("SKIP_DEPLOY", 'false') == 'true' or os.getenv("SKIP_DEPLOY", 'false') == 'True'

inputs_list = [ACTION_PATH, CLIENT_ID, CLIENT_KEY, CLIENT_REALM, TF_STATE_BUCKET_NAME, TF_STATE_REGION, IAC_BUCKET_NAME,
               IAC_REGION]
build_pipeline_url()
if None in inputs_list:
    print("- Some mandatory input is empty. Please, check the input list.")
    exit(1)

with open(Path(ACTION_PATH + '/manifest.yaml'), 'r') as file:
    manifesto_yaml = file.read()

manifesto_dict = safe_load(manifesto_yaml)

if VERBOSE is not None:
    print("- MANIFESTO:", manifesto_dict)

manifestoType = manifesto_dict["manifesto"]["kind"]
appOrInfraId = manifesto_dict["manifesto"]["spec"]["id"]

print(f"{manifestoType} project identified, with ID: {appOrInfraId}")

iam_url = f"{STACKSPOT_IAM_URL}/{CLIENT_REALM}/oidc/oauth/token"
iam_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
iam_data = {"client_id": f"{CLIENT_ID}", "grant_type": "client_credentials", "client_secret": f"{CLIENT_KEY}"}

def build_skip_url(run_id: str):
    return f"{STACKSPOT_RUNTIME_MANAGER_URL}/v3/run/self-hosted/skip-deploy/{run_id}"

def check_if_is_skippable(run_id: str, token: str):
    try: 
        url = build_skip_url(run_id)
        deploy_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.patch(
            url=url, 
            headers=deploy_headers
        )

        if response.status_code == 423: # HTTP Status Locked means SKIPPED
            return True

        response.raise_for_status() # Any other error should be raised

        return False
    except requests.HTTPError as err:
        print("An error has occurred while trying to check if deploy should be skipped")
        resp = err.response
        if resp is not None:
            print("Error code:", resp.status_code)
            if resp.content:
                try:
                    error_json = resp.json()
                    print("Status:", error_json.get("status"))
                    print("Details:", error_json.get("details"))
                except Exception as parse_err:
                    print("Failed to parse error response as JSON:", parse_err)
                    print("Raw response:", resp.text)
        else:
            print("No response")
        exit(1)

print("Authenticating...")
r1 = requests.post(
        url=iam_url, 
        headers=iam_headers, 
        data=iam_data
    )


if r1.status_code == 200:
    d1 = r1.json()
    access_token = d1["access_token"]
    
    print("Successfully authenticated!")
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

    branch = None
    if "runConfig" in manifesto_dict:
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
                    "bucket": TF_STATE_BUCKET_NAME,
                    "region": TF_STATE_REGION
                },
                "iac": {
                    "bucket": IAC_BUCKET_NAME,
                    "region": IAC_REGION
                }
            },
            "pipelineUrl": build_pipeline_url(),
        }
    )

    pipeline_url = {
        "pipelineUrl": build_pipeline_url()
    }

    request_data = json.loads(request_data)
    request_data = {
        **request_data,
        **json.loads(config_data),
        **pipeline_url,

    }

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

    if VERBOSE is not None:
        print("- DEPLOY RUN REQUEST DATA:", request_data)

    deploy_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    print("Deploying Self-Hosted...")

    if manifestoType == 'application':
        self_hosted_deploy_app_url = f"{STACKSPOT_RUNTIME_MANAGER_URL}/v1/run/self-hosted/deploy/app"
        r2 = requests.post(
                url=self_hosted_deploy_app_url, 
                headers=deploy_headers,
                data=request_data
            )
    elif manifestoType == 'shared-infrastructure':
        self_hosted_deploy_infra_url = f"{STACKSPOT_RUNTIME_MANAGER_URL}/v1/run/self-hosted/deploy/infra"
        r2 = requests.post(
                url=self_hosted_deploy_infra_url, 
                headers=deploy_headers,
                data=request_data
            )
    else:
        print("- MANIFESTO TYPE not recognized. Please, check the input.")

        exit(1)

    if r2.status_code == 201:
        d2 = r2.json()
        runId = d2["runId"]
        runType = d2["runType"]
        tasks = d2["tasks"]

        print(f"✅ - RUN {runType} successfully started with ID: {runId}")

        if SKIP_DEPLOY:
            print("Checking if run can be skipped...")
            was_skipped = check_if_is_skippable(run_id=runId, token=access_token)
            if was_skipped:
                print("✅ - Run was skipped because no changes were found.")
                tasks = []
            else:
                print("🔄 - Run was not skipped because changes were found.")

        save_output('tasks', tasks)
        save_output('run_id', runId)

    else:
        print("- Error starting self hosted deploy run")
        print("- Status:", r2.status_code)
        print("- Error:", r2.reason)
        print("- Response:", r2.text)    
        exit(1)

else:
    print("- Error during IAM authentication")
    print("- Status:", r1.status_code)
    print("- Error:", r1.reason)
    print("- Response:", r1.text)
    exit(1)
