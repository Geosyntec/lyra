#! /usr/bin/env sh

set -e

# default is to tag the image with the full version.
tag=$(grep __version__ ./lyra/lyra/__init__.py | cut -d '=' -f2 | sed 's/"//g' | tr -d '[:space:]')

while getopts t: flag
do
    case "${flag}" in
    	# user override for image tag
    	# usage:
    	#~$ push_release.sh -t 1.3.0
        t) tag=${OPTARG};;
    esac
done

if [ -z "$tag" ]
then 
    echo "building tagged release: $tag"
    bash scripts/build_prod.sh -t "$tag"
    docker-compose -f docker-stack${tag}.yml push
fi

echo "building UNtagged release (latest)"
bash scripts/build_prod.sh
docker-compose -f docker-stack.yml push
