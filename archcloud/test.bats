#!/usr/bin/env bats
#-*- shell-script -*-

export USE_LOCAL_ARCHLAB=yes
export SUBMISSION_DIR=$ARCHLAB_ROOT/../labs/CSE141pp-Lab-Test

@test "server emulation" {
    pushd $CONFIG_REPO_ROOT
    export DEPLOYMENT_MODE=EMULATION
    . config.sh
    popd

    runlab.d --just-once -v  &
    runlab --devel --solution . --directory $SUBMISSION_DIR --remote -v --lab-override repo=$SUBMISSION_DIR

    [ "$(cat $SUBMISSION_DIR/message.out)" = "yes devel" ]
    [ "$(cat $SUBMISSION_DIR/protected.out)" = 'safe!' ]
    [ "$(cat $SUBMISSION_DIR/answer.out)" = 'student answer' ]
    [ "$(cat $SUBMISSION_DIR/1.out)" = '1' ]
    [ -e $SUBMISSION_DIR/regression.out ]
    [ -e $SUBMISSION_DIR/regression.json ]
    [ -e $SUBMISSION_DIR/out.png ]
    cmp $SUBMISSION_DIR/in.png $SUBMISSION_DIR/out.png
    grep -q WallTime $SUBMISSION_DIR/code-stats.csv
}

@test "server testing" {
    pushd $CONFIG_REPO_ROOT
    export DEPLOYMENT_MODE=TESTING
    . config.sh
    popd

    runlab.d --just-once &
    runlab --devel --solution . -v --directory $SUBMISSION_DIR --remote --lab-override repo=$SUBMISSION_DIR

    [ "$(cat $SUBMISSION_DIR/message.out)" = "yes devel" ]
    [ "$(cat $SUBMISSION_DIR/protected.out)" = 'safe!' ]
    [ "$(cat $SUBMISSION_DIR/answer.out)" = 'student answer' ]
    [ "$(cat $SUBMISSION_DIR/1.out)" = '1' ]
    [ -e $SUBMISSION_DIR/regression.out ]
    [ -e $SUBMISSION_DIR/regression.json ]
    [ -e $SUBMISSION_DIR/out.png ]
    cmp $SUBMISSION_DIR/in.png $SUBMISSION_DIR/out.png
    grep -q WallTime $SUBMISSION_DIR/code-stats.csv
}


@test "server deployed" {
    pushd $CONFIG_REPO_ROOT
    export DEPLOYMENT_MODE=DEPLOYED
    . config.sh
    popd
    runlab.d --just-once &
    runlab --devel --solution . -v --directory $SUBMISSION_DIR --remote --lab-override repo=$SUBMISSION_DIR

    [ "$(cat $SUBMISSION_DIR/message.out)" = "yes devel" ]
    [ "$(cat $SUBMISSION_DIR/protected.out)" = 'safe!' ]
    [ "$(cat $SUBMISSION_DIR/answer.out)" = 'student answer' ]
    [ "$(cat $SUBMISSION_DIR/1.out)" = '1' ]
    [ -e $SUBMISSION_DIR/regression.out ]
    [ -e $SUBMISSION_DIR/regression.json ]
    [ -e $SUBMISSION_DIR/out.png ]
    cmp $SUBMISSION_DIR/in.png $SUBMISSION_DIR/out.png
    grep -q WallTime $SUBMISSION_DIR/code-stats.csv
}

