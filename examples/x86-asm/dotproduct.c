float X[1024*1024];
float Y[1024*1024];

int dotproduct(int a, int b)
{
  float s = 0;
  for(int i= 0; i < a; i++) {
    s += X[i]*Y[i];
  }
  return s;
}

int go(long int count, long int A, long int B)
{
  return dotproduct(A, B);
}
