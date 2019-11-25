@test "ls" {
      labtool --help
      labtool ls

      # submit a job but don't wait.
      date=$(date)
      runlab --directory test_inputs/tiny_lab --remote --no-validate --metadata "$date" &
      echo  sleeping
      sleep 1
      echo  killing
      kill $!
      labtool ls
      labtool ls | grep -F "$date"
}