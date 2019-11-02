
EXAMPLES=archlab_run

default: $(EXAMPLES)

include ../compile.make
../libarchlab/libarchlab.a:
	$(MAKE) -C ../libarchlab

archlab_run: archlab_run.exe
	mv $< $@

%.exe : %.o  ../libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@

.PHONY:  test
test: test_inputs/test.csv test_inputs/fail.csv
	python3 -m unittest calc.py
