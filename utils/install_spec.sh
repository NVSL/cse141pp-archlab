#!/bin/bash

if ! [ -e cpu2017-1_0_5.iso ]; then
    echo "You need cpu2017-1_0_5.iso.  It's in the google drive."
    exit 1
fi

sudo mkdir /mnt/iso
sudo mount -t iso9660 -o loop cpu2017-1_0_5.iso /mnt/iso/
cp -a /mnt/iso ./benchmarks/spec2017

cd benchmarks/spec2017
echo yes | ./install.sh
cp -a benchmarks/spec2017 benchmarks/.pristine_spec2017

patch -p3 < ../spec-CPU2017v1.0.5.patch
ln -sf ../../cse141pp.cfg config/
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

