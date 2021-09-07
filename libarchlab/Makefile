
include ../compile.make

SRCS= microbenchmarks.cpp DataCollector.cpp PAPIDataCollector.cpp PINDataCollector.cpp archlab.cpp IterationDimension.cpp

OBJS=$(SRCS:.cpp=.o)

default: libarchlab.a
setup: default
libarchlab.a: $(OBJS)
	ar rcs $@ $^

clean:  libarchlab-clean archlab-clean

libarchlab-clean:
	rm -rf *.o *.a

-include $(SRCS:.cpp=.d)
