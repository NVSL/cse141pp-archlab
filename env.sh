export ARCHLAB_ROOT=$PWD
export PIN_ROOT=$(echo $ARCHLAB_ROOT/pin-*-linux)
PATH=$PWD/tools/:$PWD/utils:$PWD/archcloud:$PIN_ROOT/:$PATH
if [ -d archcloud/venv/ ]; then
    . archcloud/venv/bin/activate
fi
