
subdirs=libarchlab cache_control pin-tools examples

.PHONY: $(subdirs)
all: $(subdirs) $(EXAMPLES)
clean: $(subdirs)

$(subdirs):
	make -C $@ $(MAKECMDGOALS)

install-prereqs:
	sudo apt-get install -y libboost-all-dev


include compile.make

