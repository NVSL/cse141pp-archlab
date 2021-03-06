#!/bin/bash


if ! [ -e cpu2017-1_0_5.iso ]; then
    echo "You need cpu2017-1_0_5.iso.  It's in the google drive."
    exit 1
fi

set -x
set -v
set -e

if which sudo; then
    SUDO=sudo
else
    SUDO=
fi

$SUDO mkdir /mnt/iso
$SUDO mount -t iso9660 -o loop cpu2017-1_0_5.iso /mnt/iso/
cp -a /mnt/iso ./benchmarks/spec2017

cd benchmarks/spec2017
echo yes | ./install.sh


(cd ../../;
 cp -a benchmarks/spec2017 benchmarks/.pristine_spec2017
)

patch -p3 < ../spec2017-setup/spec-CPU2017v1.0.5.patch
ln -sf ../../spec2017-setup/cse141pp.cfg config/
. shrc

unset ARCHLAB_RUNNER
runcpu  --config=cse141pp.cfg --size=test  --dryrun all

export ARCHLAB_RUNNER="$PWD/../../utils/simple_runner.sh $PWD/runner_ran"
rm -rf $PWD/runner_ran
runcpu  --config=cse141pp.cfg --size=test  505.mcf

if [ -e $PWD/runner_ran ]; then
    echo "Success!  The wrapper ran!"
else
    echo "Failure.  The wrapper (or the benchmarke) didn't run."
fi

