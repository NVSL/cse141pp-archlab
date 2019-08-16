export ARCHLAB_ROOT=$PWD


export PIN_ROOT=$(echo $ARCHLAB_ROOT/pin-*-linux)
PATH=$PATH:$PWD/tools/:$PWD/utils:$PIN_ROOT/
if [ -d archcloud/venv/ ]; then
    . archcloud/venv/bin/activate
fi
