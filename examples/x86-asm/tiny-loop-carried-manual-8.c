long int loop_carried(register long int n) {
  register long int s = 1;
  register long int i = 0;
  while (i < 8*n) {
    s += i;
    i++;
    s += i;
    i++;
    s += i;
    i++;
    s += i;
    i++;
    s += i;
    i++;
    s += i;
    i++;
    s += i;
    i++;
    s += i;
    i++;
  }
  return s;
}

int go(long int count, long int A, long int B)
{
  int r = 0 ;
  for(int i = 0; i < count; i++) {
     r = loop_carried(A);
  }
  return r;
}
