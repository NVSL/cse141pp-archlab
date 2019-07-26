export ARCHLAB_ROOT=$PWD
PATH=$PATH:$PWD/tools/:$PWD/utils

if [ -d archcloud/venv/ ]; then
    . archcloud/venv/bin/activate
fi
