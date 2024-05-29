# runtime-manager-action

GitHub action to authenticate and consume StackSpot Runtime API.

_**Note**: This action is supported on all runners operating systems (`ubuntu`, `macos`, `windows`)_

## 📚 Usage

### Requirements

To get the account keys (`CLIENT_ID`, `CLIENT_KEY` and `CLIENT_REALM`), please login using a **ADMIN** user on the [StackSpot Portal](https://stackspot.com), and generate new keys at [https://stackspot.com/en/settings/access-token](https://stackspot.com/en/settings/access-token).

### Use Case

```yaml
    steps:
      - uses: stack-spot/runtime-manager-action@v1
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

## License

[Apache License 2.0](https://github.com/stack-spot/runtime-manager-action/blob/main/LICENSE)
