
EXAMPLES=random_access.exe hello_world.exe side_channel.exe

default: $(EXAMPLES)

include ../compile.make
../libarchlab/libarchlab.a:
	$(MAKE) -C ../libarchlab

%.exe : %.o  ../libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@



