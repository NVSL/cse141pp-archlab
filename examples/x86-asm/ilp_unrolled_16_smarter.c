int not_unrolled(int n, int a, int b) {
	int s = 0;
	int s1 = 0;
	int s2 = 0;
	int s3 = 0;
	int s4 = 0;
	int s5 = 0;
	int s6 = 0;
	int s7 = 0;

	int i= 0;
	while (i < n) {
#define B(x, S) 	int i##x = i + x; S = S + ((a & i##x) ^ (b << i##x))
		
		B(0,s);
		B(1,s);
		B(2,s1);
		B(3,s1);

		B(4, s2);
		B(5, s2);
		B(6, s3);
		B(7, s3);

		B(8, s4);
		B(9, s4);
		B(10, s5);
		B(11, s5);

		B(12, s6);
		B(13, s6);
		B(14, s7);
		B(15, s7);
		i+=16;
	}
	return ((s + s1) + (s2 + s3)) + ((s4 + s5) + (s6 + s7));
}
