include ../../compile.make
CXX=g++-8

default: ilp_unrolled_gcc0-gv.pdf  ilp_unrolled_gcc4-gv.pdf  ilp_unrolled_gcc4unroll-gv.pdf ilp_unrolled_gcc0.trace-gv.pdf ilp_unrolled_gcc4.trace-gv.pdf \
ilp_unrolled_clang0-gv.pdf ilp_unrolled_clang1-gv.pdf  ilp_unrolled_clang2-gv.pdf  ilp_unrolled_clang3-gv.pdf 

exe: ilp_unrolled_gcc0.exe  ilp_unrolled_gcc1.exe  ilp_unrolled_clang1.exe   ilp_unrolled_clang2.exe   ilp_unrolled_clang2.exe   ilp_unrolled_clang3sse.exe  


%.exe : %.o   ilp_driver.o
	$(CXX) $(filter %.o,$^) $(LDFLAGS) -o $@


ilp_unrolled_gcc0.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_gcc1.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_gcc2.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_gcc3.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_gcc4.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_gcc4unroll.c: ilp_unrolled_1.c
	cp $< $@

ilp_unrolled_gcc0.s: C_OPTS=-O0  -mno-sse
ilp_unrolled_gcc0.s: CC=gcc-8
ilp_unrolled_gcc4.s: C_OPTS=-O4  -mno-sse
ilp_unrolled_gcc4.s:  CC=gcc-8
ilp_unrolled_gcc4unroll.s: C_OPTS=-O4 -funroll-loops -mno-sse
ilp_unrolled_gcc4unroll.s:  CC=gcc-8

ilp_unrolled_clang0.s: C_OPTS=-O1 -mno-sse
ilp_unrolled_clang0.s: CC=clang
ilp_unrolled_clang1.s: C_OPTS=-O1 -mno-sse
ilp_unrolled_clang1.s: CC=clang
ilp_unrolled_clang2.s: C_OPTS=-O2 -mno-sse
ilp_unrolled_clang2.s: CC=clang
ilp_unrolled_clang3.s: C_OPTS=-O3 -mno-sse
ilp_unrolled_clang3.s: CC=clang
ilp_unrolled_clang3sse.s: C_OPTS=-O3
ilp_unrolled_clang3sse.s: CC=clang
ilp_unrolled_clang-fast.s:  C_OPTS=-Ofast -mno-sse
ilp_unrolled_clang-fast.s:  CC=clang

ilp_unrolled_clang0.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang1.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang2.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang3.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang3sse.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang-fast.c: ilp_unrolled_1.c
	cp $< $@



ilp_unrolled_1.s: C_OPTS=-O1
ilp_unrolled_1.s:  CC=gcc-8
ilp_unrolled_4.s: C_OPTS=-O1
ilp_unrolled_4.s:  CC=gcc-8
ilp_unrolled_16.s: C_OPTS=-O1
ilp_unrolled_16.s:  CC=gcc-8
ilp_unrolled_16_smart.s: C_OPTS=-O1
ilp_unrolled_16_smart.s:  CC=gcc-8
ilp_unrolled_16_smarter.s: C_OPTS=-O1
ilp_unrolled_16_smarter.s:  CC=gcc-8
ilp_unrolled_5.s: C_OPTS=-O1
ilp_unrolled_5.s:  CC=gcc-8
ilp_unrolled_5_smart.s: C_OPTS=-O1
ilp_unrolled_5_smart.s:  CC=gcc-8
ilp_unrolled_5_smarter.s: C_OPTS=-O1
ilp_unrolled_5_smarter.s:  CC=gcc-8
