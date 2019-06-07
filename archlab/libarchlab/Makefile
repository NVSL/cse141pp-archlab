
include ../compile.make

SRCS= microbenchmarks.cpp DataCollector.cpp PCMDataCollector.cpp PAPIDataCollector.cpp PINDataCollector.cpp archlab.cpp

OBJS=$(SRCS:.cpp=.o)

default: libarchlab.a
libarchlab.a: $(OBJS)
	ar rcs $@ $^

clean: 
	rm -rf *.o *.a

-include $(SRCS:.cpp=.d)
