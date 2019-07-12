int not_unrolled(int n, int a, int b) {
	int s = 0;
	int i = 0;
#define B(x) 	 s = s + ((a & i) ^ (b << i)); i = i + 1
	switch ((n - i) % 5) {
	case 4:
		B(0);
	case 3:
		B(1);
	case 2:
		B(2);
	case 1:
		B(3);
	case 0:
		;
	}

	i += (n - i) % 5;

	while (i < n) {

		B(0);
		B(1);
		B(2);
		B(3);
		B(4);
	}
	return s;
}
