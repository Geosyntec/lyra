@ECHO off    
if /i "%1" == "" goto :help
if /i %1 == help goto :help
if /i %1 == build goto :build
if /i %1 == clean goto :clean
if /i %1 == test goto :test
if /i %1 == develop goto :develop
if /i %1 == prod goto :prod
if /i %1 == up goto :up
if /i %1 == down goto :down
if /i %1 == typecheck goto :typecheck
if /i %1 == coverage goto :coverage
if /i %1 == dev-server goto :dev-server
if /i %1 == restart goto :restart
if /i %1 == env goto :env
if /i %1 == testcors goto :testcors
if /i %1 == testget goto :testget
if /i %1 == az-login goto :az-login
if /i %1 == az-deploy goto :az-deploy

:help
echo Commands:
echo   - clean       : removes caches and old test/coverage reports
echo   - test        : runs tests and integration tests in docker
echo   - develop     : builds/rebuilds the development containers
echo   - prod        : builds/rebuilds the production containers
echo   - up          : starts containers in '-d' mode
echo   - down        : stops containers and dismounts volumes
echo   - typecheck   : runs mypy typechecker
echo   - coverage    : calculates code coverage of tests within docker
echo   - dev-server  : starts a local development server with 'reload' and 'foreground' tasks
echo.
echo Usage:
echo $make [command]
goto :eof

:build
docker-compose -f docker-stack.yml build
goto :eof

:test
call make clean
call make restart
docker-compose exec lyra-tests pytest %2 %3 %4 %5 %6
goto :eof

:typecheck
call make clean
call make restart
mypy --config-file=lyra/mypy.ini lyra
goto :eof

:develop
call make clean
call scripts\build_dev.bat
call make build
goto :eof

:prod
call make clean
call scripts\build_prod.bat
call make build
goto :eof

:up
docker-compose up -d
goto :eof

:down
docker-compose down -v
goto :eof

:clean
call scripts\clean.bat
goto :eof

:dev-server
docker-compose run -p 8080:80 lyra bash /start-reload.sh
goto :eof

:restart
docker-compose restart redis celeryworker
goto :eof

:env
scripts\make_dev_env.bat
goto :eof

:testcors
curl ^
-H "Origin: http://localhost:8880" ^
-H "Access-Control-Request-Method: GET" ^
-X OPTIONS --verbose ^
localhost:8010/api/hydstra/sites
rem -H "Access-Control-Request-Headers: X-Requested-With" ^
rem https://swn-lyra-dev.azurewebsites.net/plot/trace
rem localhost:8080/api/hydstra/sites
rem localhost:8080/api/hydstra/sites/spatial
rem https://swn-lyra-dev.azurewebsites.net/api/hydstra/sites/spatial
goto :eof

:testget
curl ^
-X GET --verbose ^
https://swn-lyra-dev.azurewebsites.net/api/hydstra/sites
rem localhost:8080/api/hydstra/sites
rem -H "Origin: http://localhost:8880" ^
rem "http://localhost:8080/api/plot/trace?site=ELTORO^&variable=11^&datasource=A^&start_date=2010-01-01^&start_time=00:00:00^&end_date=2015-01-01^&end_time=00:00:00^&data_type=tot^&interval=hour^&multiplier=1"
rem https://swn-lyra-dev.azurewebsites.net/plot/trace
rem localhost:8080/api/hydstra/sites
rem localhost:8080/api/hydstra/sites/spatial
rem https://swn-lyra-dev.azurewebsites.net/api/hydstra/sites/spatial
goto :eof

:az-login
bash scripts/login.sh
goto :eof

:az-deploy
call make az-login
call make prod
docker-compose push
goto :eof
