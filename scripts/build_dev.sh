set -e
export COMPOSE_FILE=docker-stack.yml

docker-compose \
-f docker-compose.shared.build.yml \
-f docker-compose.shared.depends.yml \
-f docker-compose.shared.env.yml \
-f docker-compose.shared.ports.yml \
-f docker-compose.dev.command.yml \
-f docker-compose.dev.ports.yml \
-f docker-compose.dev.volumes.yml \
config > docker-stack.yml
