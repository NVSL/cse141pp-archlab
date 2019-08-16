int not_unrolled(long int n, int a,int b) {
      int s = 0;
      long int i = 0;
      while (i < n*8) {
	      s = s + ((a & i) ^ (b << i));
	      i = i + 1;
      }
      return s;
}

int go(long int count, long int A, long int B)
{
  int r = 0 ;
  for(int i = 0; i < count; i++) {
    r = not_unrolled(A, B, B);
  }
  return r;
}
