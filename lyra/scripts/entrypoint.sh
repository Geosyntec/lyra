set -e

if [ "$LYRA_ENVIRONMENT" == "PRODUCTION" ] ; then
	bash /start.sh
else
	echo "run program manually"
fi
