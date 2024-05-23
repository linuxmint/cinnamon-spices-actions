#!/bin/bash

FILENAME="$1"
BACKUP_COUNT_SUFFIX=""
BACKUP_FILE_NAME=$FILENAME.bkp
GREP_REGEX='+[0-9]{0,}+$'

# since we validated if the file exists in the check process
# now we need to check if a backup file already exists
BAKUP_FILE_EXISTS=$(ls $BACKUP_FILE_NAME* -v 2>/dev/null)

# if this variable is not empty, so backup files exists in the folder
if [[ ! -z "$BAKUP_FILE_EXISTS" ]]; then


    TOTALBACKUPFILES=$(ls $BACKUP_FILE_NAME* -v | wc -l)

    # if more than one backup exists, we need to read the last number and 
    # increase it by 1 to generate the new backup file
    if (($TOTALBACKUPFILES > 0 )); then

        # get the last file but only the ones created with a number in the end
        LAST_FILE_COUNT=$(ls $BACKUP_FILE_NAME* -v | grep -oE $GREP_REGEX | tail -n 1)

        ## verify the next one to be created
        if [[ -z "$LAST_FILE_COUNT" ]]; then
            # there is a single backup file, so the next one will be 2
            BACKUP_COUNT_SUFFIX=2
        else
            # there are various bkp files, lets check and create a new one based in the last one
            ((LAST_FILE_COUNT++))
            BACKUP_COUNT_SUFFIX=$LAST_FILE_COUNT
        fi
    fi
fi

# lets create the backup file
cp $FILENAME $BACKUP_FILE_NAME$BACKUP_COUNT_SUFFIX

exit 0