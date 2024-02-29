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

### 2. Build the Docker Container

To build a Docker image, use the `build_container` argument with the provided script. This will build a Docker image using the Dockerfile located at `app/Indexing/Dockerfile`. The image will be tagged as `indexingapp:latest`.

```bash
./script.sh build_container
```
### 3. Run the Docker Container

To run the Docker container, use the run_container argument with the provided script. This command will start the Docker container and map port 8000 of your local machine to port 8000 of the container. It also sets the necessary environment variables for the application.

```bash
./script.sh run_container
```
### 4. Push Docker Image to Azure Container Registry
To upload the Docker image to Azure Container Registry, use the push_container argument with the provided script. This command will set the necessary environment variables, build the Docker image, and push it to the specified Azure Container Registry.

```bash
./script.sh push_container
```

### 5. Deploy the Application to Azure Container Apps

To deploy the application to Azure Container Apps, use the up_app argument with the provided script. This command will set the necessary environment variables, build the Docker image, and push it to the specified Azure Container Registry.

```bash
./script.sh up_app
```
