default: smt

include $(ARCHLAB_ROOT)/compile.make

$(ARCHLAB_ROOT)/libarchlab/libarchlab.a:
	$(MAKE) -C $(ARCHLAB_ROOT)/libarchlab

%.exe : %.o  $(ARCHLAB_ROOT)/libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@


smt%.exe : smt%.o  
	$(CXX) $(filter %.o,$^) $(LDFLAGS) -o $@

smt%.c: smt.c
	cp $< $@


.PHONY: smt
smt: smt-low-gv.pdf smt-high-gv.pdf smt.exe

smt%.cpp: smt.cpp
	cp $< $@

smt-low.pin-trace: TRACE_ARGS=--threads 0 --t0ilp low --iters 5
smt-high.pin-trace: TRACE_ARGS=--threads 0 --t0ilp high --iters 5
