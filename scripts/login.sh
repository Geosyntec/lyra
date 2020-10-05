#! /usr/bin/env sh

set -e
REG=$(grep AZURE_CONTAINER_REGISTRY lyra/lyra/.env | cut -d '=' -f2)
az acr login --name $REG
