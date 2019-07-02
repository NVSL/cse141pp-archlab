
EXAMPLES=archlab_run

default: $(EXAMPLES)

include ../compile.make
../libarchlab/libarchlab.a:
	$(MAKE) -C ../libarchlab

archlab_run: archlab_run.exe
	mv $< $@

%.exe : %.o  ../libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@



