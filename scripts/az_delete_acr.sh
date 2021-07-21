#! /usr/bin/env bash

set -e

# WARNING! This script deletes data!

ENABLE_DELETE=false

# TIMESTAMP can be a date-time string such as 2019-03-15T17:55:00.
REGISTRY=$(grep AZURE_CONTAINER_REGISTRY lyra/lyra/.env | cut -d '=' -f2)
TIMESTAMP=2020-07-01

while getopts t: flag
do
    case "${flag}" in
    	# set timestamp.
        t) TIMESTAMP=${OPTARG};;
    esac
done

repos=( swn/lyra swn/lyra-tests swn/flower swn/celeryworker swn/redis )
for i in "${repos[@]}"
do
	echo $i
    az acr repository show-manifests --name $REGISTRY --repository $i \
    --orderby time_asc --query "[?timestamp < '$TIMESTAMP'].{Tag:tags[0], Time:timestamp}" -o table

done

read -p "Continue with deletion of images earlier than $TIMESTAMP (y/n)?" choice
case "$choice" in 
  y|Y ) ENABLE_DELETE=true;;
  * ) echo "aborting..."; exit 0;;
esac

if [ "$ENABLE_DELETE" = true ]
then
    for i in "${repos[@]}"
    do
        echo "Deleting old images from repository $i"
        
        # Delete all images older than specified timestamp.
        az acr repository show-manifests --name $REGISTRY --repository $i \
        --orderby time_asc --query "[?timestamp < '$TIMESTAMP'].digest" -o tsv \
        | xargs -I% az acr repository delete --name $REGISTRY --image $i@% --yes
    done

fi