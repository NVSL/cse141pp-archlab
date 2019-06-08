
subdirs=libarchlab cache_control pin-tools

.PHONY: $(subdirs)
all: $(subdirs)
clean: $(subdirs)

$(subdirs):
	make -C $@ $(MAKECMDGOALS)

install-prereqs:
	sudo apt-get install -y libboost-all-dev


include compile.make
