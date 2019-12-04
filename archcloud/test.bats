#!/usr/bin/bash

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
    export DEPLOYMENT_MODE=TESTING
    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd
    
    (runlab.d --just-once -v & sleep 10; kill $!) &
    sleep 3
    pushd test_inputs/gradescope/
    rm -rf submission
    mkdir -p submission
    cp -r $LABS_ROOT/CSE141pp-Lab-Tiny/* submission/
    gradescope -v --root .
    [ -f results/results.json ]
    grep 'Some data' results/results.json
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
    export DEPLOYMENT_MODE=TESTING
    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd
    
    ! labtool # should fail without arguments
    labtool --help
    labtool ls
    labtool top --once
}

@test "hosttool" {
    export DEPLOYMENT_MODE=TESTING
    pushd $CONFIG_REPO_ROOT
    . config.sh
    popd
    
    ! hosttool # should fail without arguments
    hosttool --help
    hosttool top --once 
    hosttool ls
    hosttool cmd send-heartbeat
}
