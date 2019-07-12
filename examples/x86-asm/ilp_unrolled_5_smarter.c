int not_unrolled(int n, int a, int b) {
	int s = 0;
	int s1 = 0;
	int s2 = 0;
	int s3 = 0;
	int s4 = 0;
	int i= 0;
#define B(x, S) 	{int i##x = i + x; S = S + ((a & i##x) ^ (b << i##x));}

	switch ((n - i) % 5) {
	case 4:
		B(0,s);
	case 3:
		B(1,s);
	case 2:
		B(2,s);
	case 1:
		B(3,s);
	case 0:
		;
	}
	
	i += (n - i) % 5;


	while (i < n) {
		
		B(0,s);
		B(1,s);
		B(2,s1);
		B(3,s1);
		B(4,s1);

		i+=5;
	}
	return ((s + s1) + (s2 + s3)) + s4;
}
