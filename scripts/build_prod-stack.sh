#! /usr/bin/env sh

set -e

while getopts t: flag
do
    case "${flag}" in
        t) tag=${OPTARG};;
    esac
done

export LYRA_VERSION=$tag
echo "setting image '$LYRA_VERSION' from tag '$tag'"

docker-compose \
-f docker-compose.shared.build.yml \
-f docker-compose.shared.depends.yml \
-f docker-compose.shared.env.yml \
-f docker-compose.shared.ports.yml \
-f docker-compose.deploy.images.yml \
-f docker-compose.deploy.command.yml \
config > docker-stack${tag}.yml
