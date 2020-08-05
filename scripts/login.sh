#! /usr/bin/env sh

set -e
REG=$(grep AZURE_CONTAINER_REGISTRY .env | cut -d '=' -f2)
az acr login --name $REG
