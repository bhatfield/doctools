if [ ! $TI_ROOT ]; then
    echo "Error: \$TI_ROOT not defined!  Exiting..."
fi
sh repo_update.sh
outdir=$TI_ROOT/doctools/dist/platform/latest
rm -rf $outdir
mkdir -p $outdir
echo $outdir
cd $TI_ROOT/doctools
sh deploy.sh -o alloy -o modules -g htmlguides -d $outdir -t "Appcelerator Platform - Appcelerator Docs" prod
rm -rf ~/Sites/platform/latest
rm -rf ~/Sites/platform/landing
cp -rf $outdir ~/Sites/platform/latest
cp -rf $TI_ROOT/appc_web_docs/platform/landing ~/Sites/platform/.
