DEBUG_TEMPLATE=template
PROD_TEMPLATE=template-min
VIDEO_LIST="videos.json"
PROCESSED_VIDEO_LIST="build/videos.json"
config="./jsduck.config"
guidesdir="./htmlguides"
outdir="./dist/platform/latest"
title="Appcelerator Platform - Appcelerator Docs"

progname=$0

usage() {
    echo "Usage: $progname [options] [debug|prod]"
    echo ""
    echo "  Options:"
    echo "  -c <config_file> (i.e., jsduck_21.config for 2.1 docs build)."
    echo "  -o <optional_project> (currently 'alloy' and 'modules' are supported)"
    echo "  -g <guides_dir> (defaults to htmlguides)."
    echo "  -a <addon_guides_dir> Specified add-on guides."
    echo "  -d <output_dir> (defaults to dist/titanium/3.0)."
    echo "  -s  Enable --seo flag to jsduck."
    echo "  -t <title> Specify title for doc site."
    echo ""
}

while getopts ":so:a:c:d:g:t:" opt; do
    case $opt in 
        a)
            if [ "$OPTARG" ]; then
                addon_guidesdir=$OPTARG
            fi
            ;;
        c)
            if [ "$OPTARG" ]; then
                config=$OPTARG
            fi
            ;;
        d)
            if [ "$OPTARG" ]; then
                outdir=$OPTARG
            fi
            ;;
        o)
            if [ $OPTARG == "alloy" ]; then
                include_alloy="include_alloy"
            elif [ $OPTARG = "modules" ]; then 
                include_modules="include_modules" 
            else
                echo "Unknown optional project, $OPTARG">&2
                usage
                exit 1
            fi
            ;;
        g)
            if [ "$OPTARG" ]; then
                guidesdir=$OPTARG
            fi
            ;;
        s)  
            seo="--seo"
            ;;
        t) 
            if [ "$OPTARG" ]; then
                title="$OPTARG"
            fi
            ;;
        \?) 
             echo "Invalid option: -$OPTARG">&2
             usage
             exit 1
             ;;
        :)
             echo "Option -$OPTARG requires an argument." >&2
             usage
             exit 1
             ;;
    esac
done

# Skip the options and move on to the positional parameters
shift $((OPTIND-1))


while [ "$1" ]; do
    if [ "$1" == "prod" ]; then
        production_build="production"
        seo="--seo"
        no_thumbnails=""
    elif [ "$1" == "debug" ]; then
        debug_build="debug"
    fi
    shift
done

if [ ! "$TI_DOCS" ]; then
    if [ "$TI_ROOT" ]; then
        TI_DOCS=${TI_ROOT}/titanium_mobile/apidoc
    else
        echo "No doc root \$TI_DOCS and \$TI_ROOT not defined. Exiting."
        exit 1
    fi
fi
if [ ! "$JSDUCK" ]; then
    if [ "$TI_ROOT" ]; then
        JSDUCK=${TI_ROOT}/jsduck
    else
        echo "No JSDuck dir \$JSDUCK and \$TI_ROOT not defined. Exiting."
        exit 1
    fi
fi

if [ ! "$DOCTOOLS" ]; then
    if [ "$TI_ROOT" ]; then
        DOCTOOLS=${TI_ROOT}/doctools
    else
        echo "No doctools dir \$DOCTOOLS and \$TI_ROOT not defined. Exiting."
        exit 1
    fi
fi

if [ ! "$ALLOY" ]; then
    if [ "$TI_ROOT" ]; then
        ALLOY=${TI_ROOT}/alloy
    else
        echo "No alloy dir \$ALLOY and \$TI_ROOT not defined. Exiting."
        exit 1
    fi
fi

if [ $include_alloy ]; then
    alloyDirs="${ALLOY}/Alloy/lib ${ALLOY}/docs/apidoc ${DOCTOOLS}/add-ons
               $(find $ALLOY/Alloy/builtins -maxdepth 1 -type f ! -name moment.js)"
fi

if [ $include_modules ]; then
    if [ ! "$APPC_MODULES" ]; then
        if [ "$TI_ROOT" ]; then
            APPC_MODULES=${TI_ROOT}/appc_modules
        else
            echo "No appc_modules dir \$APPC_MODULES and \$TI_ROOT not defined. Exiting."
            exit 1
        fi
    fi
    module_dirs="$APPC_MODULES/ti.map/apidoc $APPC_MODULES/ti.facebook/apidoc
                 $APPC_MODULES/ti.nfc/apidoc $APPC_MODULES/ti.newsstand/apidoc $TIZEN_MODULE
                 $APPC_MODULES/ti.coremotion/apidoc $APPC_MODULES/ti.urlsession/apidoc
                 $APPC_MODULES/ti.touchid/apidoc"

        module_dirs+=" $APPC_MODULES/ti.geofence/apidoc $APPC_MODULES/appcelerator.https/apidoc
                       $APPC_MODULES/com.appcelerator.apm/apidoc"
fi

node ${TI_DOCS}/docgen.js -f jsduck -o ./build/ $module_dirs

if [ $addon_guidesdir ]; then
    python ./guides_merger.py --input "${guidesdir}/toc.xml" --addon "${addon_guidesdir}/toc.xml"  --output "./build/merged_guides"

    ## Workaround for new Confluence plug-in
    #cp -r $guidesdir/attachments_* ./build/merged_guides/.
    #cp -r $guidesdir/images_* ./build/merged_guides/.

    ## Attachments
    cp -r $guidesdir/attachments_* ./build/merged_guides/.
    cp -r $addon_guidesdir/attachments_* ./build/merged_guides/.

    ## Images
    cp -r $guidesdir/images ./build/merged_guides/.
    cp -r $addon_guidesdir/images ./build/merged_guides/.

    guidesdir="./build/merged_guides"
    parseropts=""
else
    parseropts="--show_edit_button"
fi
node guides_parser --input "${guidesdir}/toc.xml" --output "./build/guides" $parseropts

# Assume video list is pre-processed, with real thumbnails 
cp $VIDEO_LIST $PROCESSED_VIDEO_LIST
# After updating video list, add thumbnails manually using the video_thumbs command: 
#    python ./video_thumbs.py --input $VIDEO_LIST --output $PROCESSED_VIDEO_LIST

if [ $production_build ] ; then
    (cd ${JSDUCK}; rake compress)
    TEMPLATE=${JSDUCK}/${PROD_TEMPLATE}

    ## Generate Solr content
    echo "Generating Solr content for indexing..."
    $TI_DOCS/docgen.py -f solr -o ./build $module_dirs
    mkdir -p $outdir/../data/solr
    cp ./build/api_solr.json $outdir/../data/solr/.
    if [ $include_alloy ]; then
        echo "Generating Solr content for Alloy..."
        bash $DOCTOOLS/jsduck2json/alloy2json.sh solr
        cp ./dist/solr_api.json $outdir/../data/solr/alloy_api.json
    fi
else
    compass compile ${JSDUCK}/template/resources/sass
    TEMPLATE=${JSDUCK}/${DEBUG_TEMPLATE}
fi

ruby ${JSDUCK}/bin/jsduck --template ${TEMPLATE} $seo --output $outdir --title "$title" --config $config $alloyDirs 

# TIDOC-1327 Fix server errors
cp -r "$guidesdir/images/icons" "$outdir/resources/images/."

## Copy resources
## Workaround for new Confluence plugin
cp -r $guidesdir/attachments_* $outdir/.
#cp -r $guidesdir/images_* $outdir/.

cp -r $guidesdir/css/common.css "$outdir/resources/css/common.css"
cp -r $guidesdir/images "$outdir/images"
#cp -r $guidesdir/attachments "$outdir/attachments"

cp ./resources/mock_video.png $outdir/resources/images/mock_video.png
cp ./resources/codestrong_logo_short.png $outdir/resources/images/codestrong_logo_short.png

# Copy API images folder to $outdir
cp -r $TI_DOCS/images $outdir/.
