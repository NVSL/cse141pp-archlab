
subdirs=libarchlab cache_control pin-tools examples

.PHONY: $(subdirs)
all: $(subdirs) $(EXAMPLES)
clean: $(subdirs)

$(subdirs):
	make -C $@ $(MAKECMDGOALS)

install-papi:
	curl  http://icl.utk.edu/projects/papi/downloads/papi-5.7.0.tar.gz -o papi-5.7.0.tar.gz
	tar xzf papi-5.7.0.tar.gz
	(cd papi-5.7.0; ./configure; make; make install; make install-man)

install-pin:
	curl https://software.intel.com/sites/landingpage/pintool/downloads/pin-3.7-97619-g0d0c92f4f-gcc-linux.tar.gz -o pin-3.7-97619-g0d0c92f4f-gcc-linux.tar.gz
	tar xzf pin-3.7-97619-g0d0c92f4f-gcc-linux.tar.gz

install-prereqs: install-papi install-pin install-pcm
#	sudo apt-get install -y libboost-all-dev

install-pcm:
	(git clone https://github.com/opcm/pcm.git; cd pcm; make)

include compile.make

