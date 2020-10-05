#! /usr/bin/env sh

set -e

while getopts t: flag
do
    case "${flag}" in
        t) tag=${OPTARG};;
    esac
done

bash scripts/build_prod-stack.sh -t "$tag"
docker-compose -f docker-stack${tag}.yml build
