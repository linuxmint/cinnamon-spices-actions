#!/bin/bash

if [[ -f $1 && -x $1 ]] 
then
    exit 0
fi

exit 1
