#include <linux/module.h>
#include <linux/version.h>
#include <linux/kernel.h>
#include <linux/types.h>
#include <linux/kdev_t.h>
#include <linux/fs.h>
#include <linux/device.h>
#include <linux/cdev.h>
#include <linux/smp.h>
#include <linux/mm.h>

//#include <linux/asm/system.h>
#include <linux/smp.h>
#include "cache_control.h"

static dev_t first; // Global variable for the first device number
static struct cdev c_dev; // Global variable for the character device structure
static struct class *cl; // Global variable for the device class
#define DEVICE_NAME "cache_control"

static int my_open(struct inode *i, struct file *f)
{
  printk(KERN_INFO "Driver: open()\n");
  return 0;
}

static int my_close(struct inode *i, struct file *f)
{
  printk(KERN_INFO "Driver: close()\n");
  return 0;
}


// Copied from /arch/x86/mm/pageattr.c

static void __cpa_flush_all(void *arg)
{
  //unsigned long cache = (unsigned long)arg;
  printk("flushed a cache");
  /*
   * Flush all to work around Errata in early athlons regarding
   * large page flushing.
   */
  //SS: removed.  we don't run on athlon __flush_tlb_all();

  //SS: removed.  We run on modern x86 onlyif (cache && boot_cpu_data.x86 >= 4)
    wbinvd();
}

static void cpa_flush_all(void )
{
  BUG_ON(irqs_disabled());

  on_each_cpu(__cpa_flush_all, (void *) 0, 1);
}

static long my_ioctl(struct file *f, unsigned int cmd, unsigned long arg)
{

  switch (cmd)
    {
    case CACHE_CONTROL_FLUSH_CACHES:
      printk("Flushed the caches");
      cpa_flush_all();
      break;
    default:
      return -EINVAL;
    }

  return 0;
}

static struct file_operations pugs_fops = {
  .owner = THIS_MODULE,
  .open = my_open,
  .release = my_close,
  .unlocked_ioctl = my_ioctl
};

static int __init cache_control_init(void) 
{
  printk(KERN_INFO "cache_control registered");

  if (alloc_chrdev_region(&first, 0, 1, DEVICE_NAME) < 0)
    {
      return -1;
    }

  if ((cl = class_create(THIS_MODULE, DEVICE_NAME)) == NULL)
    {
      unregister_chrdev_region(first, 1);
      return -1;
    }

  if (device_create(cl, NULL, first, NULL, DEVICE_NAME) == NULL)
    {
      class_destroy(cl);
      unregister_chrdev_region(first, 1);
      return -1;
    }
  
  cdev_init(&c_dev, &pugs_fops);
  
  if (cdev_add(&c_dev, first, 1) == -1)
    {
      device_destroy(cl, first);
      class_destroy(cl);
      unregister_chrdev_region(first, 1);
      return -1;
    }
  return 0;
}

static void __exit cache_control_exit(void) /* Destructor */
{
  cdev_del(&c_dev);
  device_destroy(cl, first);
  class_destroy(cl);
  unregister_chrdev_region(first, 1);
  printk(KERN_INFO DEVICE_NAME " unloaded");
}

module_init(cache_control_init);
module_exit(cache_control_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Steven Swanson <swanson@cs.ucsd.edu>");
MODULE_DESCRIPTION("Exposes protected cache control mechanisms to userspace.");
