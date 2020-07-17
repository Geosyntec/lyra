set -e

if [ "$LYRA_DEPLOY_ENVIRONMENT" == "AZURE" ] ; then
	bash /start.sh
else
	echo "run program manually"
fi
