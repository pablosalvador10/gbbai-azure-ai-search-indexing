@description('The location to deploy the resources')
param location string = resourceGroup().location

@description('The environment of the project')
param environment string

@description('The name of the Container Registry')
var containerRegistryName = toLower('${environment}ContainerRegistryAigbb')

@description('Name of the Container App Environment')
param environmentName string = toLower('${environment}IndexingAzureAigbb')

@description('The container image that this container app will use')
param containerImage string = '${environment}containerregistryaigbb.azurecr.io/chunkingandindexingskill:latest'

@description('The nae of the app will use')
param containerAppName string

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
param cpuCore string = '0.25'

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
param memorySize string = '0.5'

@description('The minimum number of replicas that will be deployed. Must be at least 3 for ZR')
@minValue(1)
@maxValue(30)
param minReplica int = 1

@description('The maximum number of replicas that will be deployed')
@minValue(1)
@maxValue(30)
param maxReplica int = 3

@description('Concurrent requests allowed for the container app. Must be between 1 and 1000. Default is 100.')
param concurrentRequests string = '100'

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' existing = {
  name: environmentName
}

resource containerApp 'Microsoft.App/containerApps@2022-10-01' = {
  name: containerAppName
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Multiple'
      ingress: {
        external: true
        targetPort: 80
        allowInsecure: false
        transport: 'auto'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: [
        {
          name: 'container-registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
      registries: [
        {

          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'container-registry-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: containerImage
          env: [
            {
              name: 'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'
              value: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
            }
            {
              name: 'AZURE_DOCUMENT_INTELLIGENCE_KEY'
              value: AZURE_DOCUMENT_INTELLIGENCE_KEY
            }
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              value: AZURE_STORAGE_CONNECTION_STRING
            }
            {
              name: 'AZURE_AOAI_API_KEY'
              value: AZURE_AOAI_API_KEY
            }
            {
              name: 'AZURE_AOAI_API_ENDPOINT'
              value: AZURE_AOAI_API_ENDPOINT
            }
            {
              name: 'AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID'
              value: AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID
            }
            {
              name: 'AZURE_AOAI_API_VERSION'
              value: AZURE_AOAI_API_VERSION
            }
            {
              name: 'AZURE_AI_SEARCH_SERVICE_ENDPOINT'
              value: AZURE_AI_SEARCH_SERVICE_ENDPOINT
            }
            {
              name: 'AZURE_SEARCH_ADMIN_KEY'
              value: AZURE_SEARCH_ADMIN_KEY
            }
          ]
          resources: {
            cpu: json(cpuCore)
            memory: '${memorySize}Gi'
          }
        }
      ]
      scale: {
        minReplicas: minReplica
        maxReplicas: maxReplica
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: concurrentRequests
              }
            }
          }
        ]
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output principalId string = containerApp.identity.principalId
output tenantId string = containerApp.identity.tenantId
output id string = containerApp.id
