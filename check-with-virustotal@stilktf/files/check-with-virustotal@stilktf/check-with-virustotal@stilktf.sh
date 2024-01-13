#!/bin/bash

DOMAIN="check-with-virustotal@stilktf"
DOMAIN_DIR="${HOME}/.local/share/locale"
_NOT_FOUND=$"Couldn't find file on VirusTotal."
NOT_FOUND=$(/usr/bin/gettext "$_NOT_FOUND")

(
    HASH=($(sha256sum "$@"))
    echo $HASH
    exec 1>&-
    JSON=$(/usr/bin/curl -X POST -H "User-Agent: VirusTotal" -H "Content-Type: application/json" -d "[{\"hash\": \"${HASH}\"}]" 'https://www.virustotal.com/partners/sysinternals/file-reports?apikey=4e3202fdbe953d628f650229af5b3eb49cd46b2d3bfe5546ae3c5fa48b554e0c' | python3 -c "import sys, json; print(json.load(sys.stdin)['data'][0]['permalink'])")
    if [ $JSON ]; then
        xdg-open $JSON
    else
        /usr/bin/zenity --title="${HASH}" --text="${NOT_FOUND}" --info
    fi
)