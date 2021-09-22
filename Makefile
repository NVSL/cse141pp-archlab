subdirs=libarchlab cache_control examples tools # pin-tools 

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

insert-module:
	insmod cache_control/cache_control.ko
	modprobe msr

test:
	$(MAKE) -C tests test
	$(MAKE) -C archcloud test
	$(MAKE) -C tools test

include compile.make

