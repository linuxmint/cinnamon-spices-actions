#!/bin/bash
# downloads the language file for mediainfo
SELF_PATH=$(dirname $0)
pushd $SELF_PATH/po
lang=$(echo $LANG | sed 's/.UTF-8//')
lang_=$(echo $lang | sed 's/_/-/')
wget -O ${lang}.csv https://raw.githubusercontent.com/MediaArea/MediaInfo/master/Source/Resource/Plugin/Language/${lang_}.csv && rm 'zh-CN.csv' || mv -f ${lang_}.csv ${lang}.csv
popd