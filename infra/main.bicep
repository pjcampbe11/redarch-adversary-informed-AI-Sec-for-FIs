// main.bicep — the same estate as provision.sh, as declarative IaC.
// Field guide: Ch. 11/14/15. Deploy: az deployment group create -g rg-advisor-ai -f main.bicep
// Secure defaults: publicNetworkAccess Disabled everywhere; identity via RBAC, no keys.

param location string = resourceGroup().location
@description('Object id of the app managed identity to grant data-plane roles.')
param appManagedIdentityObjectId string

// --- Azure OpenAI ----------------------------------------------------------
resource aoai 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'voya-aoai'
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: 'voya-aoai'
    publicNetworkAccess: 'Disabled'      // Ch.15: never internet-reachable
    disableLocalAuth: true               // Ch.14: keyless only, kill API keys
  }
}

resource advisorDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aoai
  name: 'advisor-gpt4o'
  sku: { name: 'Standard', capacity: 20 } // tokens-per-minute quota (Ch.10 DoW)
  properties: {
    model: { format: 'OpenAI', name: 'gpt-4o', version: '2024-08-06' }
  }
}

// --- Azure AI Search (RAG index) ------------------------------------------
resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: 'voya-search'
  location: location
  sku: { name: 'standard' }
  properties: {
    publicNetworkAccess: 'disabled'
    authOptions: null                    // Entra-only auth (no admin keys)
    disableLocalAuth: true
  }
}

// --- Azure AI Content Safety (firewall) -----------------------------------
resource safety 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'voya-contentsafety'
  location: location
  kind: 'ContentSafety'
  sku: { name: 'S0' }
  properties: { publicNetworkAccess: 'Disabled', disableLocalAuth: true }
}

// --- Least-privilege data-plane role assignments ---------------------------
// "Cognitive Services OpenAI User" — call the model, nothing more.
resource aoaiRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aoai.id, appManagedIdentityObjectId, 'aoai-user')
  scope: aoai
  properties: {
    principalId: appManagedIdentityObjectId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}
// "Search Index Data Reader" — read the index, cannot write/rebuild.
resource searchRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, appManagedIdentityObjectId, 'search-reader')
  scope: search
  properties: {
    principalId: appManagedIdentityObjectId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '1407120a-92aa-4202-b7e9-c0e197c71c8f')
  }
}

output aoaiEndpoint string = aoai.properties.endpoint
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output contentSafetyEndpoint string = safety.properties.endpoint
