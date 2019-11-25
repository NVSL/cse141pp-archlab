@test "ls" {
      labtool --help
      labtool ls

      # submit a job but don't wait.
      date=$(date)
      runlab --directory $LABS_ROOT/CSE141pp-Lab-Tiny --remote --no-validate --metadata "$date" &
      echo  sleeping
      sleep 1
      echo  killing
      kill $!
      labtool ls
      labtool ls | grep -F "$date"
}

@test "autograder" {
      export DEPLOYMENT_MODE=EMULATION
      pushd $CONFIG_REPO_ROOT
      . config.sh
      popd
      
      runlab.d --just-once -v  &
      pushd test_inputs/gradescope/
      rm -rf submission
      mkdir -p submission
      cp -r $LABS_ROOT/CSE141pp-Lab-Tiny/* submission/
      gradescope --root .
      [ -f results/results.json ]
      grep 'Some data' results/results.json
}