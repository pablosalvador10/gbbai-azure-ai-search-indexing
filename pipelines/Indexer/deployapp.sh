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
imageName="chunkingandindexingskill" # Assuming 'chunkingindexingskill' is your Docker image name
imageTag="latest" # Replace 'latest' with your specific tag if needed
templateFile="deployment\\container-apps\\index-azure-ai-app.bicep" # Replace 'yourBicepFileName.bicep' with your Bicep file name

# Define the Azure Container Registry name
containerRegistryName="${ENVIRONMENT}containerregistryaigbb"

# Check the command line argument
case "$1" in
    build_container)
        # Build the Docker image
        docker build -f pipelines/Indexer/app/Dockerfile -t $imageName:$imageTag .
        ;;
    run_container)
        # Run the Docker container, mapping port 8000 to 8000 and setting environment variables
        docker run -p 8000:8000 \
            -e AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=$AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT \
            -e AZURE_DOCUMENT_INTELLIGENCE_KEY=$AZURE_DOCUMENT_INTELLIGENCE_KEY \
            -e AZURE_STORAGE_CONNECTION_STRING=$AZURE_STORAGE_CONNECTION_STRING \
            -e AZURE_AOAI_API_KEY=$AZURE_AOAI_API_KEY \
            -e AZURE_AOAI_API_ENDPOINT=$AZURE_AOAI_API_ENDPOINT \
            -e AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID=$AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID \
            -e AZURE_AOAI_API_VERSION=$AZURE_AOAI_API_VERSION \
            -e AZURE_AI_SEARCH_SERVICE_ENDPOINT=$AZURE_AI_SEARCH_SERVICE_ENDPOINT \
            -e AZURE_SEARCH_ADMIN_KEY=$AZURE_SEARCH_ADMIN_KEY \
            $imageName
        ;;
    push_container)
        # Non-Interactive Azure Login using Service Principal
        echo "Logging in to Azure with service principal..."
        echo "az login --service-principal -u $CLIENT_ID -p $CLIENT_SECRET --tenant $TENANT_ID"
        az login --service-principal -u $CLIENT_ID -p $CLIENT_SECRET --tenant $TENANT_ID

        # Log in to Azure Container Registry
        echo "Logging in to Azure Container Registry..."
        echo "az acr login --name $containerRegistryName.azurecr.io"
        az acr login --name $containerRegistryName.azurecr.io

        # Tag the Docker image for Azure Container Registry
        echo "Tagging Docker image for Azure Container Registry..."
        echo "docker tag $imageName:$imageTag $containerRegistryName.azurecr.io/$imageName:$imageTag"
        docker tag $imageName:$imageTag $containerRegistryName.azurecr.io/$imageName:$imageTag

        # Push the Docker image to Azure Container Registry
        echo "Pushing Docker image to Azure Container Registry..."
        echo "docker push $containerRegistryName.azurecr.io/$imageName:$imageTag"
        docker push $containerRegistryName.azurecr.io/$imageName:$imageTag
        ;;
    up_app)
        az containerapp up -n customskill --ingress external --target-port 8000 \
            --env-vars AZURE_AI_KEY=$AZURE_AI_KEY STORAGE_CONNNECTION_STRING="$STORAGE_CONNNECTION_STRING" OPENAI_API_KEY=$OPENAI_API_KEY \
            --source .
        ;;
    deploy_bicep)
        az deployment group create \
            --resource-group $RESOURCE_GROUP \
            --template-file $templateFile \
            --parameters environment=$ENVIRONMENT \
                        containerAppName=$CONTAINER_APP_NAME \
                        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=$AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT \
                        AZURE_DOCUMENT_INTELLIGENCE_KEY=$AZURE_DOCUMENT_INTELLIGENCE_KEY \
                        AZURE_STORAGE_CONNECTION_STRING=$AZURE_STORAGE_CONNECTION_STRING \
                        AZURE_AOAI_API_KEY=$AZURE_AOAI_API_KEY \
                        AZURE_AOAI_API_ENDPOINT=$AZURE_AOAI_API_ENDPOINT \
                        AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID=$AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID \
                        AZURE_AOAI_API_VERSION=$AZURE_AOAI_API_VERSION \
                        AZURE_AI_SEARCH_SERVICE_ENDPOINT=$AZURE_AI_SEARCH_SERVICE_ENDPOINT \
                        AZURE_SEARCH_ADMIN_KEY=$AZURE_SEARCH_ADMIN_KEY
        ;;
    *)
        usage
        ;;
esac
