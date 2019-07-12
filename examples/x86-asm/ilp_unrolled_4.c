int not_unrolled(int n, int a, int b) {
	int s = 0;
	int i = 0;
	while (i < n) {
		s = s + ((a & i) ^ (b << i));
		i = i + 1;
		s = s + ((a & i) ^ (b << i));
		i = i + 2;
		s = s + ((a & i) ^ (b << i));
		i = i + 3;
		s = s + ((a & i) ^ (b << i));
		i = i + 4;
	}
	return s;
}
