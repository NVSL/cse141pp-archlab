EXAMPLES=smt.exe

default: $(EXAMPLES)

include $(ARCHLAB_ROOT)/compile.make
$(ARCHLAB_ROOT)/libarchlab/libarchlab.a:
	$(MAKE) -C $(ARCHLAB_ROOT)/libarchlab

%.exe : %.o  $(ARCHLAB_ROOT)/libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@



