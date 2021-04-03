---
title: "[underTheHood]  underTheHood"
date: 2021-03-30
categories: ["underTheHood"]
tags: ["underTheHood"]
---

# UnderTheHood

这里记录一些具有高度总结性质的格言

## Page Cache

1. 主存充当两个功能,一个是进程的存储空间(堆栈),一个磁盘的缓存(page cache)

如此一来,一切都说得通了,我们常说read要从内核缓冲区拷贝到用户缓冲区,你也许和我有一样的疑惑,为什么要先拷贝到内核缓冲区呢?不能直接拷贝到用户缓冲区呢?

其实,这是属于名词的误用,这个内核缓冲区,其实不是缓冲区,而是磁盘的缓存page cache.当我们读取磁盘时,为了降低缺失率,我们会在内存中缓存磁盘的数据,这称为page cache.大部分未被分配给进程的内存都作为page cache存在.

因此,这里内核缓冲区到用户缓冲区的拷贝,实际是page cache到用户buffer的拷贝!

那为什么不直接从磁盘拷贝到用户缓冲区呢?

- 为了缓存

如果是直接拷贝到用户缓冲区,那么同时还要拷贝到page cache上,这是愚蠢的.就像cpu的cache一样,寄存器永远是从cache读数据,而不是从内存读数据,当cache缺失时,会read allocate,从内存拷贝到缓存,再从缓存拷贝到寄存器.这里也是一样的道理,从磁盘buffer拷贝到page cache,再从page cache拷贝到user buffer.(注意到磁盘也是有buffer,常称为disk buffer,是位于磁盘上的内存,用于减少io次数)