long int loop_carried(register long int n) {
  register long int s = 1;
  register long int i = 0;
  while (i < 8*n) {
    s += i;
    i++;
  }
  return s;
}
