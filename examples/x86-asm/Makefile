include ../../compile.make
CXX=g++-8

UNROLL_EXAMPLES=ilp_unrolled_gcc0-gv.pdf  ilp_unrolled_gcc4-gv.pdf  ilp_unrolled_gcc4unroll-gv.pdf ilp_unrolled_gcc0.trace-gv.pdf ilp_unrolled_gcc4.trace-gv.pdf \
ilp_unrolled_clang0-gv.pdf ilp_unrolled_clang1-gv.pdf  ilp_unrolled_clang2-gv.pdf  ilp_unrolled_clang3-gv.pdf 

RENAME_EXAMPLES=rename-unrenamed-gv.pdf dfg-gv.pdf

LOOP_CARRIED = euclid-gv.pdf euclid-trace-4-gv.pdf

default:$(UNROLL_EXAMPLES) $(RENAME_EXAMPLES) $(LOOP_CARRIED)

EXE=ilp_unrolled_gcc0.exe  ilp_unrolled_gcc1.exe  ilp_unrolled_clang1.exe   ilp_unrolled_clang2.exe   ilp_unrolled_clang2.exe    ilp_unrolled_gcc4unroll.exe # ilp_unrolled_clang3sse.exe

TRACES=ilp_unrolled_gcc0.trace-gv.pdf ilp_unrolled_gcc4.trace-gv.pdf  ilp_unrolled_clang1.trace-gv.pdf

exe: $(EXE)
keypdfs: $(patsubst %.exe,%-gv.pdf,$(EXE)) $(TRACES)
	open $^

#######################################

ilp_unrolled_%.exe : %.o  driver.o
	$(CXX) $(filter %.o,$^) $(LDFLAGS) -o $@
ilp_unrolled%.c: ilp_unrolled_1.c
	cp $< $@


ilp_unrolled_gcc0.s: C_OPTS=-O0  -mno-sse
ilp_unrolled_gcc0.s: CC=gcc-8
ilp_unrolled_gcc1.s: C_OPTS=-O4  -mno-sse
ilp_unrolled_gcc1.s:  CC=gcc-8
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

dfg.gv  : RENAME_FLAGS=--no-rename
#######################################

rename2%.asm : rename2.asm
	cp $< $@

rename2-unrenamed.gv  : RENAME_FLAGS=--no-rename
rename2-linear.gv  : RENAME_FLAGS=--no-rename --linear


euclid.s: C_OPTS=-O1
#######################################


loop-carried_%.exe : %.o  driver.o
	$(CXX) $(filter %.o,$^) $(LDFLAGS) -o $@
loop-carried%.c: loop-carried_1.c
	cp $< $@

loop-carried.s: C_OPTS=-O1
loop-carried-unroll.s: C_OPTS=-O1 -funroll-loops

#######################################

tiny-loop-carried_%.exe : %.o  driver.o
	$(CXX) $(filter %.o,$^) $(LDFLAGS) -o $@
tiny-loop-carried%.c: tiny-loop-carried_1.c
	cp $< $@

tiny-loop-carried.s: C_OPTS=-O4
tiny-loop-carried-unroll.s: C_OPTS=-O4 -funroll-loops

tiny-loop-carried-manual-8.s: C_OPTS=-O4 -mno-sse

#######################################

dp%.exe : dp%.o  drive-dp.o
	$(CXX) $(filter %.o,$^) $(LDFLAGS) -o $@

dp%.c: dp.c
	cp $< $@

dp-novec.o:C_OPTS=-O1
dp-novec.s:C_OPTS=-O1
dp-novec.pin-trace: TRACE_ARGS=--A 4

dp-novec-simplified.o:C_OPTS=-O1
dp-novec-simplified.s:C_OPTS=-O1
dp-novec-simplified.pin-trace: TRACE_ARGS=--A 3
dp-novec-simplified.gv: RENAME_FLAGS=--omit-control-edges

dp.pin-trace: TRACE_ARGS=--A 4
dp.gv: RENAME_FLAGS=

dp-0.o:C_OPTS=-O0 -fno-inline
dp-1.o:C_OPTS=-O1 -fno-inline
dp-2.o:C_OPTS=-O2 -fno-inline
dp-3.o:C_OPTS=-O3 -fno-inline
dp-3-skylake.o:C_OPTS=-O3 -march=skylake  -fno-inline

.PHONY: dp
dp: dp-0.exe dp-1.exe dp-2.exe dp-3.exe dp-3-skylake.exe


###################################

vsum%.exe : vsum%.o  drive-vsum.o
	$(CXX) $(filter %.o,$^) $(LDFLAGS) -o $@

vsum%.c: vsum.c
	cp $< $@


vsum%.s:  CC=clang
.PHONY: vsum
vsum: vsum-0.exe vsum-skylake-nounroll.exe vsum-skylake.exe vsum-1.exe

vsum-skylake.s: C_OPTS=-O3 -march=skylake -mno-avx512f
vsum-skylake-nounroll.s: C_OPTS=-O3 -march=skylake -fno-unroll-loops -mno-avx512f
vsum-0.s: C_OPTS=-O0
vsum-1.s: C_OPTS=-O1
