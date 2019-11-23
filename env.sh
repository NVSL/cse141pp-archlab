export ARCHLAB_ROOT=$PWD
export PIN_ROOT=$(echo $ARCHLAB_ROOT/pin-*-linux)
if [ -d archcloud/venv/ ]; then
    . archcloud/venv/bin/activate
fi
PATH=$PWD/tools/:$PWD/utils:$PWD/archcloud:$PIN_ROOT/:$PATH

export LD_LIBRARY_PATH=/usr/local/lib
