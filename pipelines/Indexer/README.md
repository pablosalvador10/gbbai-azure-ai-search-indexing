Custom Skill Deployment Guide
This guide will walk you through the steps to build, run, and deploy a custom skill using Docker and Azure Container Apps.

Prerequisites
Docker installed on your machine
Azure CLI installed on your machine
An Azure account
A .env file in your project root with the necessary environment variables
Steps
Load Environment Variables

The script starts by loading environment variables from a .env file located at the project root. These variables include your Azure and OpenAI credentials.

export $(grep -v '^#' ../../../../.env | xargs)

Build the Docker Image

If you run the script with the build argument, it will build a Docker image using the Dockerfile located at src/azure_search_ai/custom_skills/pdf_chunking/Dockerfile. The image will be tagged as customskill.

./script.sh build


Run the Docker Container

If you run the script with the run argument, it will run the Docker container, mapping port 8000 of your machine to port 8000 of the container. It also sets the necessary environment variables.

./script.sh run


Deploy to Azure Container Apps

If you run the script with the up argument, it will deploy the application to Azure Container Apps. It sets the necessary environment variables and specifies the source directory for the deployment.

./script.sh up
