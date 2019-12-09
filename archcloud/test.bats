#!/bin/sh

if check-deployed; then
    export MODES=EMULATION
else
    export MODES=EMULATION CLOUD
fi

@test "ls" {
    labtool --help
    labtool ls

    # submit a job but don't wait.
    date=$(date)
    runlab --directory $LABS_ROOT/CSE141pp-Lab-Tiny --remote --no-validate &
    echo  sleeping
    sleep 1
    echo  killing
    kill $!
    labtool ls
}


@test "autograder" {
    # Test the autograding script
    # This should mimic how our gradescope scripts run it.
    # Tests for the setup stuff is the autograder repo.

    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd
    export MODES=EMULATION
    for LAB in CSE141pp-Lab-Test; do 
	for CLOUD_MODE in $MODES; do
	    reconfig
	    (runlab.d --just-once -v & sleep 15; kill $!) &
	    sleep 3
	    pushd test_inputs/gradescope/
	    rm -rf submission
	    mkdir -p submission
	    cp -r $LABS_ROOT/$LAB/* submission/
	    gradescope -v --root .
	    [ "$(jextract score  < results/results.json)" == "0.0" ]
	    jextract tests -1 name  < results/results.json | grep GradedRegressions
	done
    done
}

@test "local tools" {
    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd

    for CLOUD_MODE in $MODES; do
	reconfig
	(runlab.d -v --heart-rate 0.5 --id foobar & sleep 10; kill $!) &
	sleep 1
	hosttool top --once -v 2>&1 | tee t
	grep foobar t
	hosttool cmd send-heartbeat
    done
}

@test "packet" {
    if [ "$PACKET_PROJECT_ID" = "" ]; then
	skip
    fi
    hosttool ls
}

@test "job flow" {
    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd
    for CLOUD_MODE in $MODES; do
	reconfig
	(runlab.d --just-once -v & sleep 10; kill $!) &
	sleep 3
	pushd $LABS_ROOT/$TESTING_LAB
	runlab --remote --pristine
	popd
    done
}

@test "jextract" {
    echo '{"a": "b"}' | jextract a
    echo '{"a": ["b", "c"]}' | jextract a 0
    [ $(echo '["a","b"]' | jextract 1) = "b" ]  
    ! echo '{"a": "b"}' | jextract c
}

@test "freqs" {
    get-cpu-freqs
    eval `get-cpu-freqs`
    echo $ARCHLAB_AVAILABLE_CPU_FREQUENCIES;
    (t=$(which get-cpu-freqs); PATH=; $t)
    eval `(t=$(which get-cpu-freqs); PATH=; $t)`
    [ "$ARCHLAB_AVAILABLE_CPU_FREQUENCIES" = "" ]

    set-cpu-freq 1000
    # there's some tabs in cpuinfo that makes grepping a pain
    perl -ne 's/\s+/ /g; print' < /proc/cpuinfo | grep -q 'cpu MHz : 1000.'
    set-cpu-freq max
}

@test "labtool" {
    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd
    
    for CLOUD_MODE in $MODES; do
	! labtool # should fail without arguments
	labtool --help
	labtool ls
	labtool top --once
    done
}

@test "hosttool" {
    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd

    for CLOUD_MODE in $MODES; do
	! hosttool # should fail without arguments
	hosttool --help
	hosttool top --once 
	hosttool ls
	hosttool cmd send-heartbeat
    done
}
