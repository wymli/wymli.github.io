---
title: "[sys] 虚拟内存与缓存缓冲"
date: 2021-03-30
categories : []
tag: ["OS-Memory"]
---

# 虚拟内存virtual memory

什么是虚拟内存,应该不用多言.本质就是一个逻辑的虚拟地址空间,这些地址空间中,有的地址真正的对应到了物理内存的地址,有的地址却是对应到了磁盘上的地址(通过swap交换换页进入物理内存).

对进程来说,虚拟内存屏蔽了底层的物理内存和外存,为进程提供简洁易用的接口.

进程持有的虚拟地址会经过内存管理单元(mmu,memory management unit)转变为物理地址,然后访问物理内存.

> 主存的随机访问速度是磁盘的100K倍,但是顺序访问速度却只是磁盘的10倍(因此某些服务比如kafka,redis在持久化时,会采用aof文件顺序写)

## 虚拟页

虚拟内存以页作为基本组织单位,一般一个页4KB.

页有三种状态:

- 未分配
- 未缓存
- 已缓存

显然,其中未缓存和已缓存都代表已分配.未缓存指的是该虚拟内存指向了磁盘上的地址,尚未交换到物理内存,而已缓存指的是已加载到物理内存

当用户访问未被缓存的物理页时,触发缺页中断,于是被访问页被加载到物理内存上

> 页表存储了虚拟内存到物理内存的映射,每个PCB都有一个页表指针,即每个进程都拥有一个自己的页表

## 交换区

磁盘上不是所有空间都能被虚拟地址空间映射的,我们专门在磁盘上划分了一个交换区.这里的数据可以被页面调度或交换

## 页面调度和交换

页面调度指的是物理内存上的单个物理页是否和磁盘上交换区的物理页交换(页面swap)

交换一般指整个进程的交换,是一种进程状态,表示整个进程在内存中的映像都换到了外存

不过一般来说,一次页面调度也是一次页的交换

## 无图无真相

```go
cat /proc/cpuinfo
address sizes   : 39 bits physical, 48 bits virtual
```



```go
liwm29@lwm:/mnt/c/WINDOWS/system32$ free
              total        used        free      shared  buff/cache   available
Mem:        6399360       72100     6284536          68       42724     6180340
Swap:       2097152           0     2097152
```

```go
liwm29@lwm:/mnt/c/WINDOWS/system32$ cat /proc/meminfo
MemTotal:        6399360 kB
MemFree:         6253264 kB
MemAvailable:    6164212 kB
Buffers:            9564 kB
Cached:            49864 kB
SwapCached:            0 kB
Active:            23280 kB
Inactive:          38232 kB
Active(anon):       2156 kB
Inactive(anon):        8 kB
Active(file):      21124 kB
Inactive(file):    38224 kB
Unevictable:           0 kB
Mlocked:               0 kB
SwapTotal:       2097152 kB
SwapFree:        2097152 kB
Dirty:               252 kB
Writeback:             0 kB
AnonPages:          2056 kB
Mapped:             4092 kB
Shmem:                68 kB
Slab:              27232 kB
SReclaimable:      13536 kB
SUnreclaim:        13696 kB
KernelStack:        1808 kB
PageTables:          168 kB
NFS_Unstable:          0 kB
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:     5296832 kB
Committed_AS:       7256 kB
VmallocTotal:   34359738367 kB
VmallocUsed:           0 kB
VmallocChunk:          0 kB
Percpu:             1888 kB
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
ShmemPmdMapped:        0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
Hugetlb:               0 kB
DirectMap4k:       17408 kB
DirectMap2M:     3446784 kB
DirectMap1G:     4194304 kB
```

## 共享内存

我们知道线程(pthread_create)之间是共享全局变量的,而进程(fork)之间是不共享的,这是为什么呢?

其内部就是虚拟内存有关,当调用fork后,子进程会copy父进程的页表,所以此时它们指向了同样的物理内存空间,如果使用clone(),使用`CLONE_VM `参数,那么它们就真的共享同一个内存空间了,否则的化,会触发写时复制

## page cache

虚拟内存将主存看成是磁盘的缓存,所以叫cache

## DRAM与SRAM

dram指内存,sram指cpu与内存之间的高速缓存,比如L1 cache,L2 cache...

## Page cache & Disk buffer

首先是cache和buffer的区别

- cache是缓存,加快读的速率
- buffer是缓冲,主要是为了减少io次数,进行批量读和批量写

> In computing, a **page cache**, sometimes also called [disk cache](https://en.wikipedia.org/wiki/Disk_cache_(disambiguation)),[[1\]](https://en.wikipedia.org/wiki/Page_cache#cite_note-1) is a transparent [cache](https://en.wikipedia.org/wiki/Cache_(computing)) for the [pages](https://en.wikipedia.org/wiki/Page_(computer_memory)) originating from a [secondary storage](https://en.wikipedia.org/wiki/Secondary_storage) device such as a [hard disk drive](https://en.wikipedia.org/wiki/Hard_disk_drive) (HDD) or a [solid-state drive](https://en.wikipedia.org/wiki/Solid-state_drive) (SSD).  The [operating system](https://en.wikipedia.org/wiki/Operating_system) keeps a page cache in otherwise unused portions of the [main memory](https://en.wikipedia.org/wiki/Main_memory) (RAM), resulting in quicker access to the contents of cached pages and  overall performance improvements.  A page cache is implemented in [kernels](https://en.wikipedia.org/wiki/Kernel_(computer_science)) with the [paging](https://en.wikipedia.org/wiki/Paging) memory management, and is mostly transparent to applications.
>
> Usually, all physical memory not directly allocated to applications is  used by the operating system for the page cache. Since the memory would  otherwise be idle and is easily reclaimed when applications request it,  there is generally no associated performance penalty and the operating  system might even report such memory as "free" or "available".

> The disk buffer is physically distinct from and is used differently from the [page cache](https://en.wikipedia.org/wiki/Page_cache) typically kept by the [operating system](https://en.wikipedia.org/wiki/Operating_system) in the computer's [main memory](https://en.wikipedia.org/wiki/Main_memory). The disk buffer is controlled by the microcontroller in the hard disk  drive, and the page cache is controlled by the computer to which that  disk is attached. The disk buffer is usually quite small, ranging  between 8 and 256 [MiB](https://en.wikipedia.org/wiki/Mebibyte), and the page cache is generally all unused main memory. While data in  the page cache is reused multiple times, the data in the disk buffer is  rarely reused

也就是说,对于主存没有直接分配的内存,那么就都是作为page cache存在(注意区分malloc和read)

也就是说,主存有两个功能,一个是作为进程的存储空间(malloc),一个是作为磁盘的page cache

所谓的那些零拷贝技术里面常讲的内核缓冲区,其实就是page cache