#!/bin/bash

if ! [ -d "$HOME/ecoacoustics-dashboard/" ]; then
    echo 'repo does not exist!'
    exit 1
fi

cd $HOME/ecoacoustics-dashboard/
git pull
if [ $? != 0 ]; then
    echo "git pull failed, check the server logs!"
    exit 1
fi

cd $HOME/ecoacoustics-dashboard/ecoacousticsDashboard/
docker compose up --build -d
if [ $? != 0 ]; then
    echo "docker compose failed, check the server logs!"
    exit 1
fi
