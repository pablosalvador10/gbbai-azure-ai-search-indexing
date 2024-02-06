#!/bin/bash

# Function to display usage
function usage() {
    echo "Usage: $0 {build|run|up}"
    exit 1
}

# Check if command line argument is provided
if [ $# -eq 0 ]; then
    usage
fi

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Define variables for Docker image name and tag
imageName="indexingskill" # Assuming 'indexingskill' is your Docker image name
imageTag="latest" # Replace 'latest' with your specific tag if needed

# Define the Azure Container Registry name
registryName="deploymentsdevregistry"

# Check the command line argument
case "$1" in
    build_container)
        # Build the Docker image
        docker build -f app/Indexer/Dockerfile -t $imageName:$imageTag .
        ;;
    run_container)
        # Run the Docker container, mapping port 8000 to 8000 and setting environment variables
        docker run -p 8000:8000 \
            -e AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=$AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT \
            -e AZURE_DOCUMENT_INTELLIGENCE_KEY=$AZURE_DOCUMENT_INTELLIGENCE_KEY \
            -e AZURE_STORAGE_CONNECTION_STRING=$AZURE_STORAGE_CONNECTION_STRING \
            -e AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY \
            -e AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
            -e AZURE_OPENAI_DEPLOYMENT_EMBEDDING=$AZURE_OPENAI_DEPLOYMENT_EMBEDDING \
            -e AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION \
            -e AZURE_AI_SEARCH_SERVICE_ENDPOINT=$AZURE_AI_SEARCH_SERVICE_ENDPOINT \
            -e AZURE_SEARCH_ADMIN_KEY=$AZURE_SEARCH_ADMIN_KEY \
            $imageName
        ;;
    push_container)
        # Non-Interactive Azure Login using Service Principal
        az login --service-principal -u $CLIENT_ID -p $CLIENT_SECRET --tenant $TENANT_ID

        # Log in to Azure Container Registry
        az acr login --name $registryName

        # Tag the Docker image for Azure Container Registry
        docker tag $imageName:$imageTag $registryName.azurecr.io/$imageName:$imageTag

        # Push the Docker image to Azure Container Registry
        docker push $registryName.azurecr.io/$imageName:$imageTag
        ;;
    up_app)
        az containerapp up -n customskill --ingress external --target-port 8000 \
            --env-vars AZURE_AI_KEY=$AZURE_AI_KEY STORAGE_CONNNECTION_STRING="$STORAGE_CONNNECTION_STRING" OPENAI_API_KEY=$OPENAI_API_KEY \
            --source .
        ;;
    *)
        usage
        ;;
esac
