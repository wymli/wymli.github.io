---
title: "[mem] Buddy system"
date: 2021-03-26T12:23:27+08:00
tags : ["mem"]
categories : ["mem"]
---

### Buddy system

linux底层使用buddy-system+slab

>  slab位于buddy-system的上层

伙伴系统是一种基于二分的动态分区算法,一开始他有k大小的空间,当有新的内存申请到达时,他会对k进行二分,直到满足那个大小恰好是最合适的大小时,返回给用户.比如,申请18KB内存,伙伴系统最初是128KB,那么会一直二分成32KB,16KB,发现16<18,所以返回给用户32KB的大小,这造成了很大的内部碎片

伙伴系统的合并机制只能合并由同一个区块分裂的子区块,对于相邻的由不同区块分裂的子区块,不能合并

> [ref](https://www.cs.fsu.edu/~engelen/courses/COP402003/p827.pdf)
>
> In a buddy system, the entire memory space available for allocation is initially treated as a single block whose size is a power of 2. When the first request is made, if its size is greater than half of the initial block then the entire block is allocated. Otherwise, the block is split in two equal companion buddies. If the size of the request is greater than half of one of the buddies, then allocate one to it. Otherwise,one of the buddies is split in half again. This method continues until the smallest block greater than or equal to the size of the request is found and allocated to it
>
> In this method, when a process terminates the buddy block that was allocated to it is freed. Whenever possible, an unmallocated buddy is merged with a companion buddy in order to form a larger free block. Two blocks are said to be companion buddies if they resulted from the split of the same direct parent block.

![image-20210326124822783](/posts/static/image-20210326124822783.png)

这里,A=70K代表分配A, A ends代表回收A

### 如何实现

逻辑很清楚了,现在的问题是怎么去记录哪些区块是分配了的,哪些是没分配的呢?

如果单纯的是一个内存池的话,我们可以直接再申请一个内存空间去存储bitmap,来代表分配回收情况. 当然也可以直接在这片内存上划出一个区域放置bitmap

但bitmap只适合固定分区的情况,对于动态分区,还要维护分区的大小

>  [from wiki](https://en.wikipedia.org/wiki/Buddy_memory_allocation)
>
>  Typically the buddy memory allocation system is implemented with the use of a [binary tree](https://en.wikipedia.org/wiki/Binary_tree) to represent used or unused split memory blocks. The "buddy" of each block can be found with an [exclusive OR](https://en.wikipedia.org/wiki/Exclusive_OR) of the block's address and the block's size.

 建议阅读:

1. https://people.kth.se/~johanmon/ose/assignments/buddy.pdf
2. https://www.cs.au.dk/~gerth/papers/actainformatica05.pdf

### find buddy

我们知道,每一个区块都有一个唯一的buddy(伙伴),并且有一个很快速的方法可以得到其伙伴的首地址

如果一个区块a大小是2^k,首地址是&a,那么它的伙伴就一定是&a+2^k或&a-2^k,因为伙伴之间的大小一定是相等的.

&a+2^k或&a-2^k,等价于直接flip(&a,k+1),翻转第k+1位(从右边开始数,从1开始计数)[前提是一定的内存对齐条件]

## 隐式free-list

所谓的隐式free-list,指的是node不维护指针,而只维护自己的大小,由于内存的连续性,自己的首地址+大小,便找到了下一个node,每个node有一个标志位决定其是否已被分配

## 显式free-list

隐式free-list的缺点是我们要遍历所有的node去寻找未分配的node

显式free-list则显式的使用指针作为其头部字段,将所有的未分配的node连在一起

## 变长分配

现在我们认为一个free-list就存储一个特定大小的node的节点集合,对于不同的大小,我们使用不同的free-list

对于每个内存区域区块的大小,我们预先定义好,但是并不是按2的n次幂 ,因为这样会造成严重的内部碎片(比如需要65,却分配了128)

因此,free-list其实是某种静态分配策略,而buddy则是半动态的