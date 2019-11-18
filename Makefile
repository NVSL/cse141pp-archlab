subdirs=libarchlab cache_control pin-tools examples tools

.PHONY: $(subdirs)
all: $(subdirs) $(EXAMPLES)
clean: $(subdirs)

$(subdirs):
	make -C $@ $(MAKECMDGOALS) PIN_ROOT=$(PWD)/pin-3.11-97998-g7ecce2dac-gcc-linux

install-papi:
	curl  http://icl.utk.edu/projects/papi/downloads/papi-5.7.0.tar.gz -o papi-5.7.0.tar.gz
	tar xzf papi-5.7.0.tar.gz
	(cd papi-5.7.0/src; ./configure --with-components=rapl; make; make install; make install-man)

install-pin:
	curl https://software.intel.com/sites/landingpage/pintool/downloads/pin-3.11-97998-g7ecce2dac-gcc-linux.tar.gz -o pin-3.11-97998-g7ecce2dac-gcc-linux.tar.gz
	tar xzf pin-3.11-97998-g7ecce2dac-gcc-linux.tar.gz

install: install-prereqs
install-prereqs: create-venv install-papi install-pin install-pcm 

create-venv:
	rm -rf archcloud/venv
	virtualenv -p `which python3` archcloud/venv
	(. archcloud/venv/bin/activate; cd archcloud/; pip install -e .)

install-pcm:
	(git clone https://github.com/opcm/pcm.git; cd pcm; make)

setup:
	insmod cache_control/cache_control.ko
	modprobe msr

test:
	$(MAKE) -C archcloud test

include compile.make

