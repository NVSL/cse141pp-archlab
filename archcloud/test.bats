#!/usr/bin/env bats
#-*- shell-script -*-

export RUN_LOCAL_DS=yes
export USE_LOCAL_ARCHLAB=yes
export RUN_LOCAL_PUBSUB=yes
export SUBMISSION_DIR=$ARCHLAB_ROOT/../labs/Test
export PUBSUB_DIR=$SUBMISSION_DIR/com/ps
export DATA_STORE_DIR=$SUBMISSION_DIR/com/ds

rm -rf $PUBSUB_DIR
rm -rf $DATA_STORE_DIR
mkdir -p $PUBSUB_DIR
mkdir -p $DATA_STORE_DIR

@test "server" {
    packet_server.py  --just-once &
    GPROF=yes run.py  --devel --solution . --directory $SUBMISSION_DIR --remote  --lab-override repo=$SUBMISSION_DIR

    [ "$(cat $SUBMISSION_DIR/message.out)" = "yes devel" ]
    [ "$(cat $SUBMISSION_DIR/protected.out)" = 'safe!' ]
    [ "$(cat $SUBMISSION_DIR/answer.out)" = 'student answer' ]
    [ "$(cat $SUBMISSION_DIR/1.out)" = '1' ]
    [ -e $SUBMISSION_DIR/code.gprof ]
    [ -e $SUBMISSION_DIR/regression.out ]
    [ -e $SUBMISSION_DIR/regression.json ]
    [ -e $SUBMISSION_DIR/out.png ]
    cmp $SUBMISSION_DIR/in.png $SUBMISSION_DIR/out.png
    grep -q WallTime $SUBMISSION_DIR/code-stats.csv
}

