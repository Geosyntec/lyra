
call docker-compose ^
-f docker-compose.shared.env.yml ^
-f docker-compose.shared.ports.yml ^
-f docker-compose.deploy.images.yml ^
-f docker-compose.deploy.command.yml ^
config > deploy-stack.yml

