
EXAMPLES=random_access.exe hello_world.exe side_channel.exe enumeration.exe

default: $(EXAMPLES)
setup: default

include ../compile.make
../libarchlab/libarchlab.a:
	$(MAKE) -C ../libarchlab

%.exe : %.o  ../libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@



