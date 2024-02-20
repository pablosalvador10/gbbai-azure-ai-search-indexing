// Define parameters for the deployment
@description('Provide a 2-13 character prefix for all resources.')
param ResourcePrefix string

@description('Location for all resources.')
param Location string = resourceGroup().location

@allowed([
  'keys'
  'rbac'
])
param authType string = 'keys'

@description('Name of Azure OpenAI Resource')
param AzureOpenAIResource string = '${ResourcePrefix}oai'

@description('Azure OpenAI Embedding Model Deployment Name')
param AzureOpenAIEmbeddingModel string = 'text-embedding-ada-002'

@description('Azure OpenAI GPT Model Name')
param AzureOpenAIEmbeddingModelName string = 'text-embedding-ada-002'

@description('Azure OpenAI GPT Model Version')
param AzureOpenAIEmbeddingModelVersion string = '2'

@description('Azure AI Search Resource')
param AzureCognitiveSearch string = '${ResourcePrefix}-search'

@description('Name of Storage Account')
param StorageAccountName string = '${ResourcePrefix}str'

@description('The SKU of the search service you want to create. E.g. free or standard')
@allowed([
  'free'
  'basic'
  'standard'
  'standard2'
  'standard3'
])
param AzureCognitiveSearchSku string = 'standard'

@description('Azure Form Recognizer Name')
param FormRecognizerName string = '${ResourcePrefix}-formrecog'

@description('Azure Form Recognizer Location')
param FormRecognizerLocation string = Location

var BlobContainerName = 'documents'

// Create an Azure OpenAI resource
resource OpenAI 'Microsoft.CognitiveServices/accounts@2021-10-01' = {
  name: AzureOpenAIResource
  location: Location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: AzureOpenAIResource
  }
  identity: {
    type: 'SystemAssigned'
  }

  // Create an Azure OpenAI Embedding Deployment resource
  resource OpenAIEmbeddingDeployment 'deployments@2023-05-01' = {
    name: AzureOpenAIEmbeddingModelName
    properties: {
      model: {
        format: 'OpenAI'
        name: AzureOpenAIEmbeddingModel
        version: AzureOpenAIEmbeddingModelVersion
      }
    }
    sku: {
      name: 'Standard'
      capacity: 30
    }
  }
}

// Create an Azure Cognitive Search resource
resource AzureCognitiveSearch_resource 'Microsoft.Search/searchServices@2022-09-01' = {
  name: AzureCognitiveSearch
  location: Location
  tags: {
    deployment: 'chatwithyourdata-sa'
  }
  sku: {
    name: AzureCognitiveSearchSku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    authOptions: authType == 'keys' ? {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    } : null
    disableLocalAuth: authType == 'keys' ? false : true
    replicaCount: 1
    partitionCount: 1
  }
}

// Create an Azure Form Recognizer resource
resource FormRecognizer 'Microsoft.CognitiveServices/accounts@2022-12-01' = {
  name: FormRecognizerName
  location: FormRecognizerLocation
  sku: {
    name: 'S0'
  }
  kind: 'FormRecognizer'
  identity: {
    type: 'None'
  }
  properties: {
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
  }
}

// Assign the Cognitive Services OpenAI Contributor role to the Search resource
module openAiContributorRoleSearch 'security/role.bicep' = if (authType == 'rbac') {
  scope: resourceGroup()
  name: 'openai-contributor-role-search'
  params: {
    principalId: AzureCognitiveSearch_resource.identity.principalId
    roleDefinitionId: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
    principalType: 'ServicePrincipal'
  }
}

// The rest of the resources (StorageAccount, BlobContainer, etc.) are not defined in the provided script.
// Please ensure to define them before using them in the script.

resource StorageAccount 'Microsoft.Storage/storageAccounts@2021-08-01' = {
  name: StorageAccountName
  location: Location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_GRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
  }
}

resource StorageAccountName_BlobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-08-01' = {
  name: '${StorageAccountName}/default/${BlobContainerName}'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    StorageAccount
  ]
}

resource StorageAccountName_config 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-08-01' = {
  name: '${StorageAccountName}/default/config'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    StorageAccount
  ]
}
