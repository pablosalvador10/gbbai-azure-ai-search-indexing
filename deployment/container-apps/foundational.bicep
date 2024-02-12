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
var containerRegistryName = toLower('${environment}ContainerRegistryAigbb')

@description('The name of the Key Vault')
var keyVaultName = replace('${trim(environment)}-KeyVault-ai-app-${trim(version)}', '\r', '')

@description('Name of the Container App Environment')
param environmentName string = toLower('${environment}IndexingAzureAigbb')

// Resource - Application Insights
@description('Name of the log analytics workspace')
param logAnalyticsName string = toLower('${environment}IndexinglogAzureAigbb')

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

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-12-01-preview' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output keyVaultUri string = keyVault.properties.vaultUri
output logAnalyticsCustomerId string = logAnalyticsWorkspace.properties.customerId
output containerAppEnvironmentId string = containerAppEnvironment.id
