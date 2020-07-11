
call scripts/build_prod.bat

call docker-compose ^
-f docker-compose.shared.env.yml ^
-f docker-compose.shared.ports.yml ^
-f docker-compose.deploy.images.yml ^
config > deploy-stack.yml

