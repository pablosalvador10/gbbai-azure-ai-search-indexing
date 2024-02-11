# Custom Skill Deployment Guide

This guide provides step-by-step instructions on how to build, run, and deploy a custom skill using Docker and Azure Container Apps.

## Prerequisites

Before you start, make sure you have the following:

- Docker installed on your machine
- Azure CLI installed on your machine
- An active Azure account
- A `.env` file in your project root with the necessary environment variables

## Deployment Steps

### 1. Load Environment Variables

Load the environment variables from your `.env` file.

- For Unix-like systems (Linux/macOS), you can use:

        ```bash
        export $(grep -v '^#' .env | xargs)
        ```

- For Windows systems, you might need to manually set each environment variable using:

        ```powershell
        $env:PROJECT_NAME="indexingapp"
        $env:ENVIRONMENT="dev"
        $env:RESOURCE_GROUP="rg-applications-$env:ENVIRONMENT"
        ```

### 2. Assign AcrPull Role

Assign the `AcrPull` role to your service principal to allow it to connect to the registry and pull images from it. Run the following command:

    ```bash
    #!/bin/bash
    # Modify for your environment. The ACR_NAME is the name of your Azure Container
    # Registry, and the SERVICE_PRINCIPAL_ID is the service principal's 'appId' or
    # one of its 'servicePrincipalNames' values.
    ACR_NAME=devContainerRegistry001
    SERVICE_PRINCIPAL_ID=5d2fcd14-d9f8-4df6-b823-e53a7de1ee55

    # Populate value required for subsequent command args
    ACR_REGISTRY_ID=$(az acr show --name $ACR_NAME --query id --output tsv)

    # Assign the desired role to the service principal. Modify the '--role' argument
    # value as desired:
    # acrpull:     pull only
    # acrpush:     push and pull
    # owner:       push, pull, and assign roles
    az role assignment create --assignee $SERVICE_PRINCIPAL_ID --scope $ACR_REGISTRY_ID --role acrpush
    ```

  > **Note:** If you're using Git Bash on Windows and encountering issues with path translation, you can use the following workaround. Git Bash automatically translates Unix-style paths to Windows paths, which can cause issues with Azure CLI commands. To temporarily disable this path translation for a command, set the `MSYS_NO_PATHCONV` environment variable to `1`:

    ```bash
    MSYS_NO_PATHCONV=1 az role assignment create --assignee $CLIENT_ID --role AcrPush --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$REGISTRY_NAME
    ```

### 3. Building the Docker Image

To build a Docker image, use the `build` argument with the provided script. This will build a Docker image using the Dockerfile located at `src/azure_search_ai/custom_skills/pdf_chunking/Dockerfile`. The image will be tagged as `customskill`.

```bash
./script.sh build
```

### 4. Running the Docker Container

To run the Docker container, use the `run` argument with the provided script. This command will start the Docker container and map port 8000 of your local machine to port 8000 of the container. It also sets the necessary environment variables for the application.

```bash
./script.sh run
```

### 5. Uploading Docker Image to Azure Container Registry

To upload the Docker image to Azure Container Registry, use the `up` argument with the provided script. This command will set the necessary environment variables, build the Docker image, and push it to the specified Azure Container Registry.

```bash
./script.sh up
```
