@description('The location to deploy the resources')
param location string = resourceGroup().location

@description('The name of the project')
param projectName string

@description('The environment of the project')
param environment string

@description('The version of the project')
param version string

@description('The prefix for resource names')
var resourcePrefix = toLower(replace(replace('${trim(projectName)}-${trim(environment)}', '\r', ''), ' ', '-'))

@description('The name of the Container Registry')
var containerRegistryName = replace('${trim(environment)}ContainerRegistry${trim(version)}', '\r', '')

@description('The name of the Key Vault')
var keyVaultName = replace('${trim(environment)}-KeyVault-ai-app-${trim(version)}', '\r', '')

@description('The name of the Application Insights')
var applicationInsightsName = replace('${trim(environment)}-AppInsights-${trim(version)}', '\r', '')

// Resource - Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2021-06-01-preview' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Resource - Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2021-06-01-preview' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
  }
}

// Resource - Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output keyVaultUri string = keyVault.properties.vaultUri
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
