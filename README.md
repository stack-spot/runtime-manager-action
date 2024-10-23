# runtime-manager-action

[![Action test Ubuntu](https://github.com/stack-spot/runtime-manager-action/actions/workflows/action-test-ubuntu.yaml/badge.svg)](https://github.com/stack-spot/runtime-manager-action/actions/workflows/action-test-ubuntu.yaml) [![Action test MacOS](https://github.com/stack-spot/runtime-manager-action/actions/workflows/action-test-macos.yaml/badge.svg)](https://github.com/stack-spot/runtime-manager-action/actions/workflows/action-test-macos.yaml) [![Action test Windows](https://github.com/stack-spot/runtime-manager-action/actions/workflows/action-test-windows.yaml/badge.svg)](https://github.com/stack-spot/runtime-manager-action/actions/workflows/action-test-windows.yaml)

GitHub action to authenticate and consume StackSpot Runtime API.

_**Note**: This action is supported on all runners operating systems (`ubuntu`, `macos`, `windows`)_

## 📚 Usage

### Requirements

To get the account keys (`CLIENT_ID`, `CLIENT_KEY` and `CLIENT_REALM`), please login using a **ADMIN** user on the [StackSpot Portal](https://stackspot.com), and generate new keys at [https://stackspot.com/en/settings/access-token](https://stackspot.com/en/settings/access-token).

### Use Case

```yaml
    steps:
      - uses: stack-spot/runtime-manager-action@v2.1
        id: run
        with:
          CLIENT_ID: ${{ secrets.CLIENT_ID }}
          CLIENT_KEY: ${{ secrets.CLIENT_KEY }}
          CLIENT_REALM: ${{ secrets.CLIENT_REALM }}
          WORKSPACE: my_workspace
          ENVIRONMENT: my_environment
          VERSION_TAG: my_tag
          TF_STATE_BUCKET_NAME: my_bucket
          TF_STATE_REGION: region
          IAC_BUCKET_NAME: my_bucket
          IAC_REGION: region
          VERBOSE: true # not mandatory
          BRANCH: main # not mandatory
          OPEN_API_PATH: swagger.yaml # not mandatory
          DYNAMIC_INPUTS: --key1 value1 --key2 value2
          WORKDIR: ./my-folder # not mandatory

      - name: Check Run Tasks Data
        run: echo "Tasks = ${{ steps.run.outputs.tasks }}"
        shell: bash
```

* * *

## ▶️ Action Inputs

Field | Mandatory | Default Value | Observation
------------ | ------------  | ------------- | -------------
**CLIENT_ID** | YES | N/A | [StackSpot](https://stackspot.com/en/settings/access-token) Client ID.
**CLIENT_KEY** | YES | N/A |[StackSpot](https://stackspot.com/en/settings/access-token) Client KEY.
**CLIENT_REALM** | YES | N/A |[StackSpot](https://stackspot.com/en/settings/access-token) Client Realm.
**WORKSPACE** | YES | N/A | StackSpot Workspace where the project has been registered.
**ENVIRONMENT** | YES | N/A | StackSpot Environment where the project will be deployed.
**VERSION_TAG** | YES | N/A | Deploy version tag
**TF_STATE_BUCKET_NAME** | YES | N/A | AWS S3 Bucket name where the generated tfstate files will be stored.
**TF_STATE_REGION** | YES | N/A | AWS region where the TF State will be stored (e.g: `us-east-1`).
**IAC_BUCKET_NAME** | YES | N/A | AWS S3 Bucket name where the generated IaC files will be stored.
**IAC_REGION** | YES | N/A | AWS region where the IaC will be stored (e.g: `us-east-1`).
**VERBOSE** | NO | `false` | Whether to show extra logs during execution. (e.g: `true`).
**BRANCH** | NO | N/A | Repository branch to checkout if necessary (e.g: `main`).
**OPEN_API_PATH** | NO | N/A | Path to OpenAI / Swagger file within the repository (e.g: `path/to/file.yml`)
**DYNAMIC_INPUTS** | NO | N/A | Dynamic inputs used with Jinja on IAC, informed as `--key1 value1 --key2 value2`
**WORKDIR** | NO | ./ | Path to the directory where the `.stk` is located.

* * *

### More information on some inputs

<details>

<summary> BRANCH </summary>

When the input `BRANCH` is used, within the IAC step of the tasks, the repository will be cloned within the `terraform.zip` with the following structure, in case repository files are necessary within terraform.

_**Note**: the contents of the branch input don't really matter, the branch cloned will be the branch used to dispatch the workflow as long as it is not empty_

```
├── main.tf
├── outputs.tf
├── repodir
│   ├── .git/
│   ├── .stk/
│   │   └── stk.yaml
│   ├── src/
│   ├── tests/
│   └── ... {repository-files}
└── variables.tf
└── ... {templates-deploy}
```

</details>

<details>

<summary> DYNAMIC_INPUTS </summary>

When the input `DYNAMIC_INPUTS` is used, the flags passes in these inputs will be added to every plugin applied as their input, and could be used by Jinja engine to modify the IaC file created

**e.g:**

`DYNAMIC_INPUTS = --app_repository="https://github.com/stack-spot/runtime-manager-action"`


_main.tf_
```jinja
{% if app_repository is defined %}
    resource_source  = {{ app_repository }}
{% else %}
    resource_source  = "default"
{% endif %}
```

</details>


<details>

<summary> WORKDIR </summary>

When the input `WORKDIR` is used, it should point to the path where a `.stk` folder is located and that it should be used as the source of the new deployment. This is specially useful if you contain multiple Stackspot infras within a single repository.

**e.g:**
`WORKDIR="./ecr-infra"` will deploy the *stk.yaml* within that folder, but if you want to deploy the *application*, you should use `WORKDIR="./application"`

**Repository structure**
```
├── .git/
├── ecr-infra/
│   ├── .stk/
│   │   └── stk.yaml
├── application/
│   ├── .stk/
│   │   └── stk.yaml
│   ├── src/
│   ├── tests/
│   └── ...
└── README.MD
```


</details>

## License

[Apache License 2.0](https://github.com/stack-spot/runtime-manager-action/blob/main/LICENSE)
