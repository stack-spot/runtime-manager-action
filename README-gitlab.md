# GitLab CI/CD Workflow for Runtime Manager Action

This GitLab CI/CD workflow runs the Runtime Manager Action with the specified parameters.

## Inputs

The following environment variables must be configured in your GitLab CI/CD settings:

- `CLIENT_ID`: Account client id (required)
- `CLIENT_KEY`: Account client secret key (required)
- `CLIENT_REALM`: Account client realm (required)
- `WORKSPACE`: Workspace used to deploy (required)
- `ENVIRONMENT`: Environment used to deploy (required)
- `VERSION_TAG`: Deploy version tag (required)
- `BRANCH`: Branch to perform checkout in Runtime (optional)
- `OPEN_API_PATH`: Path to API file to publish on StackSpot Catalog API (optional)
- `TF_STATE_BUCKET_NAME`: Bucket to save generated tfstate files (required)
- `TF_STATE_REGION`: Region configuration for tfstate (required)
- `IAC_BUCKET_NAME`: Bucket to save generated iac files (required)
- `IAC_REGION`: Region configuration for iac (required)
- `VERBOSE`: Verbose configuration (optional)
- `DYNAMIC_INPUTS`: --key1 value1 --key2 value2 (optional, default: "")
- `WORKDIR`: Path to the directory where the .stk is located. (optional, default: "./")

## Usage

To use this workflow, add the above environment variables to your GitLab CI/CD settings and include the `.gitlab-ci.yml` file in your repository.

```yaml
include:
  - local: '.gitlab-ci.yml'