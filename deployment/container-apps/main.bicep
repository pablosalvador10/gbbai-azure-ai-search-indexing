@description('The location to deploy the resources')
param location string = resourceGroup().location

@description('The name of the project')
param projectName string

@description('The environment of the project')
param environment string

@description('The version of the project')
param version string

@description('The name of the Container Registry')
var containerRegistryName = toLower('${environment}ContainerRegistryAigbb')

@description('The container app environment id to deploy to this container app to')
param containerAppEnvId string

@description('The container image that this container app will use')
param containerImage string

@description('Azure Document Intelligence Endpoint')
param AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT string

@description('Azure Document Intelligence Key')
param AZURE_DOCUMENT_INTELLIGENCE_KEY string

@description('Azure Storage Connection String')
param AZURE_STORAGE_CONNECTION_STRING string

@description('Azure AOAI API Key')
param AZURE_AOAI_API_KEY string

@description('Azure AOAI API Endpoint')
param AZURE_AOAI_API_ENDPOINT string

@description('Azure AOAI Embedding Deployment ID')
param AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID string

@description('Azure AOAI API Version')
param AZURE_AOAI_API_VERSION string

@description('Azure AI Search Service Endpoint')
param AZURE_AI_SEARCH_SERVICE_ENDPOINT string

@description('Azure Search Admin Key')
param AZURE_SEARCH_ADMIN_KEY string

@description('The tags applied to this container app resource')
param tags object = {}

@description('Number of CPU cores the container can use. Can be with a maximum of two decimals.')
@allowed([
  '0.25'
  '0.5'
  '0.75'
  '1'
  '1.25'
  '1.5'
  '1.75'
  '2'
])
param cpuCore string

@description('Amount of memory (in gibibytes, GiB) allocated to the container up to 4GiB. Can be with a maximum of two decimals. Ratio with CPU cores must be equal to 2.')
@allowed([
  '0.5'
  '1'
  '1.5'
  '2'
  '3'
  '3.5'
  '4'
])
param memorySize string

@description('The minimum number of replicas that will be deployed. Must be at least 3 for ZR')
@minValue(1)
@maxValue(30)
param minReplica int

@description('The maximum number of replicas that will be deployed')
@minValue(1)
@maxValue(30)
param maxReplica int

@description('Concurrent requests allowed for the container app. Must be between 1 and 1000. Default is 100.')
param concurrentRequests string

@description('Concurrent requests allowed for the container app. Must be between 1 and 1000. Default is 100.')
param containerAppName string

module projectResources './foundational.bicep' = {
  name: 'projectResourcesDeployment'
  params: {
    location: location
    projectName: projectName
    environment: environment
    version: version
  }
}

module indexApp './index-azure-ai-app.bicep' = {
  name: 'IndexContainerAppDeployment'
  dependsOn: [
    projectResources
  ]
  params: {
    location: location
    containerAppEnvId: containerAppEnvId
    containerRegistryName: containerRegistryName
    containerImage: containerImage
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
    AZURE_DOCUMENT_INTELLIGENCE_KEY: AZURE_DOCUMENT_INTELLIGENCE_KEY
    AZURE_STORAGE_CONNECTION_STRING: AZURE_STORAGE_CONNECTION_STRING
    AZURE_AOAI_API_KEY: AZURE_AOAI_API_KEY
    AZURE_AOAI_API_ENDPOINT: AZURE_AOAI_API_ENDPOINT
    AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID: AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID
    AZURE_AOAI_API_VERSION: AZURE_AOAI_API_VERSION
    AZURE_AI_SEARCH_SERVICE_ENDPOINT: AZURE_AI_SEARCH_SERVICE_ENDPOINT
    AZURE_SEARCH_ADMIN_KEY: AZURE_SEARCH_ADMIN_KEY
    tags: tags
    cpuCore: cpuCore
    memorySize: memorySize
    minReplica: minReplica
    maxReplica: maxReplica
    concurrentRequests: concurrentRequests
    containerAppName: containerAppName
  }
}
