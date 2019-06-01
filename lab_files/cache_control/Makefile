obj-m += cache_control.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

test.exe: test.c
	$(CC) -g -Wall -Werror -I. $< -o $@
