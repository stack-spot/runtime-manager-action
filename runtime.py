import os
import requests
import yaml
import json
from pathlib import Path

ACTION_PATH = os.getenv("ACTION_PATH")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_KEY = os.getenv("CLIENT_KEY")
CLIENT_REALM = os.getenv("CLIENT_REALM")
VERSION_TAG = os.getenv("VERSION_TAG")
TF_STATE_BUCKET_NAME = os.getenv("TF_STATE_BUCKET_NAME")
TF_STATE_REGION = os.getenv("TF_STATE_REGION")
IAC_BUCKET_NAME = os.getenv("IAC_BUCKET_NAME")
IAC_REGION = os.getenv("IAC_REGION")

inputs_list = [ACTION_PATH, CLIENT_ID, CLIENT_KEY, CLIENT_REALM, VERSION_TAG, TF_STATE_BUCKET_NAME, TF_STATE_REGION, IAC_BUCKET_NAME, IAC_REGION]

if None in inputs_list:
    print("Some input is empty")
    exit()

with open(Path(ACTION_PATH+'/manifest-app.yaml'), 'r') as file:
    manifesto_yaml = file.read()

manifesto_dict = yaml.safe_load(manifesto_yaml)

print("MANIFESTO", manifesto_dict)

manifestoType = manifesto_dict["kind"]
if manifestoType == 'application':
    appOrInfraId=manifesto_dict["spec"]["appId"]
if manifestoType == 'shared_infrastructure':
    appOrInfraId=manifesto_dict["spec"]["infraId"]
print(f"{manifestoType} project identified, with ID: {appOrInfraId}")

idm_url = f"https://idm.stackspot.com/realms/{CLIENT_REALM}/protocol/openid-connect/token"
idm_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
idm_data = { "client_id":f"{CLIENT_ID}", "grant_type":"client_credentials", "client_secret":f"{CLIENT_KEY}" }

r1 = requests.post(
        url=idm_url, 
        headers=idm_headers, 
        data=idm_data
    )

if r1.status_code == 200:
    d1 = r1.json()
    access_token = d1["access_token"]
    
    envId = manifesto_dict["spec"]["appliedPlugins"][0]["inputs"]["stk_env_id"]
    wksId = manifesto_dict["spec"]["appliedPlugins"][0]["inputs"]["stk_wks_id"]  

    request_data = json.dumps(
        {
            "config": {
                "tfstate": {
                "bucket": TF_STATE_BUCKET_NAME,
                "region": TF_STATE_REGION
                }
                # },
                # "iac": {
                #     "bucket": IAC_BUCKET_NAME,
                #     "region": IAC_REGION
                # }
            },
            "isApi": False,                      # FOR NOW
            "apiContractPath": "./swagger.yaml", # FOR NOW
            "envId": envId,
            "workspaceId": wksId,
            "versionTag": VERSION_TAG,
        }
    )
    request_data = json.loads(request_data)
    manifesto_data = json.dumps({"manifesto": manifesto_dict})
    merged_dict = {**request_data, **manifesto_data}
    request_data = json.dumps(merged_dict)

    print("Deploy request", request_data)
    
    deploy_headers = {"Authorization": f"Bearer {access_token}"}

    if manifestoType == 'application':
        self_hosted_deploy_app_url="https://runtime-manager.v1.stackspot.com/v1/run/self-hosted/deploy/app"
        r2 = requests.post(
                url=self_hosted_deploy_app_url, 
                headers=deploy_headers,
                data=request_data
            )
    if manifestoType == 'shared_infrastructure':
        self_hosted_deploy_infra_url="https://runtime-manager.v1.stackspot.com/v1/run/self-hosted/deploy/infra"
        r2 = requests.post(
                url=self_hosted_deploy_infra_url, 
                headers=deploy_headers,
                data=request_data
            )

    if r2.status_code == 201:
        d2 = r2.json()
        runId = d2["runId"]
        runType = d2["runType"]
        tasks = d2["tasks"]

        output_file = os.getenv('GITHUB_OUTPUT')
        with open(output_file, "a") as myfile:
            myfile.write(f"runId={runId}")
            myfile.write(f"runType={runType}")
            myfile.write(f"tasks={tasks}")

        print(f"Run {runType} successfully started with ID: {runId}")

    else:
        print("Error starting self hosted deploy")
        print("Status", r2.status_code)
        print("Error", r2.reason)
        exit(1)

else:
    print("Error during authentication")
    print("Status", r1.status_code)
    print("Error", r1.reason)
    exit(1)


def convert_manifesto_to_request(manifesto: str):
    with open('config.json', 'w') as json_file:
        json.dump(manifesto, json_file)
    return json.dumps(json.load(open('config.json')), indent=2)
