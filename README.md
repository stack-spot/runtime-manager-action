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
      - uses: stack-spot/runtime-manager-action@v1
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

      - name: Check Run Tasks Data
        run: echo "Tasks = ${{ steps.run.outputs.tasks }}"
        shell: bash
```



## License

[Apache License 2.0](https://github.com/stack-spot/runtime-manager-action/blob/main/LICENSE)