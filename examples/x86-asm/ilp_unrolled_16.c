int not_unrolled(int n, int a, int b) {
	int s = 0;
	int i = 0;
	while (i < n) {
#define B(x) 	 s = s + ((a & i) ^ (b << i)); i = i + 1
		B(0);
		B(1);
		B(2);
		B(3);
		B(4);
		B(5);
		B(6);
		B(7);
		B(8);
		B(9);
		B(10);
		B(11);
		B(12);
		B(13);
		B(14);
		B(15);
	}
	return s;
}
