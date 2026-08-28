#!/usr/bin/env bash
# provision.sh — stand up the Azure estate the code expects, securely by default.
# Field guide: Ch. 11 (Azure OpenAI) + Ch. 14 (identity) + Ch. 15 (networking).
#
# Every resource is created with PUBLIC NETWORK ACCESS DISABLED and the app's
# managed identity granted DATA-plane (least-privilege) roles only. Run in bash
# with the Azure CLI logged in (az login).
set -euo pipefail

RG=${RG:-rg-advisor-ai}
LOC=${LOC:-eastus}
AOAI=${AOAI:-voya-aoai}
SEARCH=${SEARCH:-voya-search}
SAFETY=${SAFETY:-voya-contentsafety}
APP_MI_OBJECT_ID=${APP_MI_OBJECT_ID:?set APP_MI_OBJECT_ID to the app managed identity object id}

az group create -n "$RG" -l "$LOC" 1>/dev/null

# --- Azure OpenAI: keyless-ready, public access OFF (Ch.11/15) --------------
az cognitiveservices account create -n "$AOAI" -g "$RG" --kind OpenAI --sku S0 \
  --location "$LOC" --custom-domain "$AOAI" \
  --api-properties '{"publicNetworkAccess":"Disabled"}'

az cognitiveservices account deployment create -n "$AOAI" -g "$RG" \
  --deployment-name advisor-gpt4o \
  --model-name gpt-4o --model-version 2024-08-06 --model-format OpenAI \
  --sku-name Standard --sku-capacity 20        # capacity = tokens-per-minute quota

# --- Azure AI Search: the RAG index (public access OFF) (Ch.13/15) ----------
az search service create -n "$SEARCH" -g "$RG" --sku standard \
  --public-network-access disabled

# --- Azure AI Content Safety: the firewall (Ch.05/06/07) --------------------
az cognitiveservices account create -n "$SAFETY" -g "$RG" --kind ContentSafety \
  --sku S0 --location "$LOC" \
  --api-properties '{"publicNetworkAccess":"Disabled"}'

# --- Least-privilege DATA-plane roles for the app managed identity (Ch.14) --
aoai_id=$(az cognitiveservices account show -n "$AOAI" -g "$RG" --query id -o tsv)
az role assignment create --assignee "$APP_MI_OBJECT_ID" \
  --role "Cognitive Services OpenAI User" --scope "$aoai_id"          # call the model

search_id=$(az search service show -n "$SEARCH" -g "$RG" --query id -o tsv)
az role assignment create --assignee "$APP_MI_OBJECT_ID" \
  --role "Search Index Data Reader" --scope "$search_id"             # read the index only

echo "Provisioned. Next: create private endpoints for each resource + private DNS,"
echo "then set the endpoints from 'az ... show' into your .env (see .env.example)."
