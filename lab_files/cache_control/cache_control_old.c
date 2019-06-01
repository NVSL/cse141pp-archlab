#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Steven Swanson");
MODULE_DESCRIPTION("Module to expose privilaged CPU cache control mechanisms.");
MODULE_VERSION("0.1");

static int major_num;
static struct class *misc_class;

#define DEVICE_NAME "cache_control"

/* Called when a process opens our device */
static int device_open(struct inode *inode, struct file *file) {
  try_module_get(THIS_MODULE);
  return 0;
}

/* Called when a process closes our device */
static int device_release(struct inode *inode, struct file *file) {
  module_put(THIS_MODULE);
  return 0;
}

static struct file_operations file_ops = {
  .open = device_open,
  .release = device_release
};


static int __init cache_control_init(void) {
  /* Try to register character device */
  misc_class = class_create(THIS_MODULE, "misc");
  err = PTR_ERR(misc_class);
  if (IS_ERR(misc_class))
    goto fail;

  major_num = register_chrdev(0, DEVICE_NAME, &file_ops);
  misc_class->devnode = misc_devnode;
  return 0;

 fail:
  pr_err("unable to get major number for cache_control devices\n");
  class_destroy(misc_class);
  return -EIO;
  
}
static void __exit cache_control_exit(void) {
class_destroy(misc_class);
}

module_init(cache_control_init);
module_exit(cache_control_exit);
