include ../../compile.make
CXX=g++-8

default:  ilp_unrolled_1-gv.pdf ilp_unrolled_4-gv.pdf ilp_unrolled_16-gv.pdf ilp_trace_16-gv.pdf ilp_unrolled_16_smart-gv.pdf ilp_unrolled_16_smarter-gv.pdf ilp_unrolled_gcc0-gv.pdf ilp_unrolled_gcc1-gv.pdf ilp_unrolled_gcc2-gv.pdf ilp_unrolled_gcc3-gv.pdf ilp_unrolled_gcc4-gv.pdf ilp_unrolled_16-gv.pdf ilp_unrolled_5_smart-gv.pdf ilp_unrolled_5_smarter-gv.pdf ilp_unrolled_5-gv.pdf

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

ilp_unrolled_gcc0.S: C_OPTS=-O0 -funroll-loops -mno-sse
ilp_unrolled_gcc0.S: CC=gcc-8
ilp_unrolled_gcc1.S: C_OPTS=-O1 -funroll-loops -mno-sse
ilp_unrolled_gcc1.S:  CC=gcc-8
ilp_unrolled_gcc2.S: C_OPTS=-O2 -funroll-loops -mno-sse
ilp_unrolled_gcc2.S:  CC=gcc-8
ilp_unrolled_gcc3.S: C_OPTS=-O3 -funroll-loops -mno-sse
ilp_unrolled_gcc3.S:  CC=gcc-8
ilp_unrolled_gcc4.S: C_OPTS=-O4 -funroll-loops -mno-sse
ilp_unrolled_gcc4.S:  CC=gcc-8

ilp_unrolled_clang0.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang1.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang2.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang3.c: ilp_unrolled_1.c
	cp $< $@
ilp_unrolled_clang-fast.c: ilp_unrolled_1.c
	cp $< $@

ilp_unrolled_clang0.c: C_OPTS=-O0
ilp_unrolled_clang0.c: CC=clang
ilp_unrolled_clang1.c:  C_OPTS=-O1
ilp_unrolled_clang1.c:  CC=clang
ilp_unrolled_clang2.c:  C_OPTS=-O2
ilp_unrolled_clang2.c: CC=clang
ilp_unrolled_clang3.c:  C_OPTS=-O3
ilp_unrolled_clang3.c: CC=clang
ilp_unrolled_clang-fast.c:  C_OPTS=-Ofast
ilp_unrolled_clang-fast.c:  CC=clang


ilp_unrolled_1.S: C_OPTS=-O1
ilp_unrolled_1.S:  CC=gcc-8
ilp_unrolled_4.S: C_OPTS=-O1
ilp_unrolled_4.S:  CC=gcc-8
ilp_unrolled_16.S: C_OPTS=-O1
ilp_unrolled_16.S:  CC=gcc-8
ilp_unrolled_16_smart.S: C_OPTS=-O1
ilp_unrolled_16_smart.S:  CC=gcc-8
ilp_unrolled_16_smarter.S: C_OPTS=-O1
ilp_unrolled_16_smarter.S:  CC=gcc-8
ilp_unrolled_5.S: C_OPTS=-O1
ilp_unrolled_5.S:  CC=gcc-8
ilp_unrolled_5_smart.S: C_OPTS=-O1
ilp_unrolled_5_smart.S:  CC=gcc-8
ilp_unrolled_5_smarter.S: C_OPTS=-O1
ilp_unrolled_5_smarter.S:  CC=gcc-8
