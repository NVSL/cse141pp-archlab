int not_unrolled(long int n, int a,int b) {
      int s = 0;
      long int i = 0;
      while (i < n) {
	      s = s + ((a & i) ^ (b << i));
	      i = i + 1;
      }
      return s;
}
