
subdirs=libarchlab cache_control pin-tools

.PHONY: $(subdirs)
all: $(subdirs)
clean: $(subdirs)

$(subdirs):
	make -C $@ $(MAKECMDGOALS)


include compile.make
