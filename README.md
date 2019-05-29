# Speeding up Dot Product

In this lab you will optimize the performance of computing the dot-product of two vectors:

```
double dot_product(double *A, double *B, int len) {
       double s = 0;
       for (int i = 0; i < len; i++) {
       	   s = s + A[i] * B[i];
       }
       return s
}
```

Dot-product is a fundamental operation in linear algebra, machine learning, scientific computing, and other applications.

## Tasks to Complete

Copy the code in `starter_code/code.c` into `submission/code.c` and modify it to go as fast as posssible.

## Testing Your Code

To run your code, do

```make submission/code.out```

