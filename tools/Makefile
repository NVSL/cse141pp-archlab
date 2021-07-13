
EXAMPLES=archlab_run archlab_check

default: $(EXAMPLES)
setup: default
include ../compile.make
../libarchlab/libarchlab.a:
	$(MAKE) -C ../libarchlab

archlab_run: archlab_run.exe
	mv $< $@

archlab_check: archlab_check.exe
	mv $< $@

%.exe : %.o  ../libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@

.PHONY:  test
test: test_inputs/test.csv test_inputs/fail.csv
	python3 -m unittest calc.py
