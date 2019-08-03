#include<stdio.h>
#include<cache_control.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <assert.h>
#include <sys/ioctl.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char * argv[]) {

  int fd = open("/dev/cache_control", O_RDWR);
  
  if (fd == -1) {
    printf("Couldn't open '/dev/cache_control' to flush caches: %s\n",  strerror(errno));
    exit(1);
  }
  
  int r = ioctl(fd, CACHE_CONTROL_FLUSH_CACHES);
  if (r == -1) {
    printf("Couldn't flush caches: %s\n",  strerror(errno));
    exit(1);
  }
  
  return 1;
}

