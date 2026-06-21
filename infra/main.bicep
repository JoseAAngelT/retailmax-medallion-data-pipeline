@description('Azure region where resources will be deployed.')
param location string = resourceGroup().location

@description('Environment name.')
param environment string = 'dev'

@description('Storage account name. Must be globally unique, lowercase and between 3 and 24 characters.')
param storageAccountName string

@description('Key Vault name. Must be globally unique.')
param keyVaultName string

@description('Log Analytics Workspace name.')
param logAnalyticsName string

@description('Action Group name for basic alerting.')
param actionGroupName string

@description('Email address used for alert notifications.')
param alertEmailAddress string

var projectName = 'retailmax-medallion-data-pipeline'

var containerNames = [
  'bronze'
  'silver'
  'gold'
  'evidence'
]

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
  tags: {
    project: projectName
    environment: environment
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: storageAccount
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for containerName in containerNames: {
    name: containerName
    parent: blobService
    properties: {
      publicAccess: 'None'
    }
  }
]

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    publicNetworkAccess: 'Enabled'
  }
  tags: {
    project: projectName
    environment: environment
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
  tags: {
    project: projectName
    environment: environment
  }
}

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: actionGroupName
  location: 'Global'
  properties: {
    groupShortName: 'retailmax'
    enabled: true
    emailReceivers: [
      {
        name: 'primary-email'
        emailAddress: alertEmailAddress
        useCommonAlertSchema: true
      }
    ]
  }
  tags: {
    project: projectName
    environment: environment
  }
}

output storageAccountOutput string = storageAccount.name
output containersOutput array = containerNames
output keyVaultOutput string = keyVault.name
output logAnalyticsOutput string = logAnalytics.name
output actionGroupOutput string = actionGroup.name