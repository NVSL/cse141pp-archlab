subdirs=libarchlab cache_control pin-tools examples tools

.PHONY: $(subdirs)
all: $(subdirs) $(EXAMPLES)
clean: $(subdirs)

ifndef ARCHLAB_ROOT
$(error ARCHLAB_ROOT is not set.  Have you sourced config.sh?  Maybe do it again.)
endif

ifndef PIN_ROOT
$(error PIN_ROOT is not set.  Have you sourced config.sh?  Maybe do it again.)
endif

setup: $(subdirs) #install-papi 

$(subdirs):
	make -C $@ $(MAKECMDGOALS)

install-papi:
	curl  http://icl.utk.edu/projects/papi/downloads/papi-5.7.0.tar.gz -o papi-5.7.0.tar.gz
	tar xzf papi-5.7.0.tar.gz
	(cd papi-5.7.0/src; ./configure --prefix $(ARCHLAB_ROOT)/installed --with-components=rapl; make utils; make install-lib) #; make install-man)

#install-pin:
#	curl https://software.intel.com/sites/landingpage/pintool/downloads/pin-3.11-97998-g7ecce2dac-gcc-linux.tar.gz -o pin-3.11-97998-g7ecce2dac-gcc-linux.tar.gz
#	tar xzf pin-3.11-97998-g7ecce2dac-gcc-linux.tar.gz


insert-module:
	insmod cache_control/cache_control.ko
	modprobe msr

test:
	$(MAKE) -C tests test
	$(MAKE) -C archcloud test
	$(MAKE) -C tools test

include compile.make

