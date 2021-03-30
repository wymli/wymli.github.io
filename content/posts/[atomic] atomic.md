---
title: "[atomic] atomic"
date: 2021-03-25
tags: ["atomic"]
categories: ["atomic"]
weight: 1
---

# 关于RMW与Atomic LD/ST

[TOC]

事情的起因是我在记录自己学习设计模式的过程时,看了sync.Once的源码,其实以前也看了很多遍,但今天一看,突然发现自己不是很懂atomic.LoadUint32()的意义,于是促成了这篇文章

## atomic.LoadUint32()

关于`atomic.LoadUint32`意义在哪里?和普通的读有什么区别?

> 原子性: 要么发生,要么不发生

> 荐读:
>
> http://www.1024cores.net/home/lock-free-algorithms/so-what-is-a-memory-model-and-how-to-cook-it
>
> https://preshing.com/20130618/atomic-vs-non-atomic-operations/

## 原子指令分类

有两类原子指令:

- RMW: read-modify-write
  - compare and swap(CAS)
    - 或相似的load-linked/store-conditional, LL/SC(解决了CAS的ABA问题)
  - fetch and add(FAA)
    - atomic.AddUint32(&sum, 1)
    - 为什么有个fetch?因为要更改值,必须先加载到寄存器或ALU,再更改,所以先fetch
- loads and stores
  - 即关于load和store的原子性
    - atomic.LoadUint32()
    - atomic.StoreUint32()

对于RMW类指令,很好理解,可以解决经典的对线程对sum++的竞态问题(比如使用FAA),那么load&store这两个指令呢?

在一些stackoverflow的回答中,我了解到,对于内存对齐的32位数,是自然提供原子读写的,通过这个,我们大概了解到原子读写是指的能否一次性通过总线把数据从内存中读写出来,但是,如果不提供原子性,危害在哪里?

## 原子性缺失证明

### 双MOV

证实: 对如下代码使用386的32位指令集架构,在amd64下交叉编译,可以看到,一个return语句确实分成了两个汇编指令

> 对go语言,交叉编译异常简单,只要设置GOOS和GOARCH即可

```go
func b() uint64 {
	var a uint64 = 0
	a = 0x900000008
	return a
}

0x0012 00018 (a.go:6)      MOVL    $8, "".~r0+4(SP)
0x001a 00026 (a.go:6)      MOVL    $9, "".~r0+8(SP)
```

### 非原子单条汇编指令

在一些cpu架构上(即一些指令集上),即使只有单条指令,也无法保证原子性

比如 __ARMv7__ 指令

```assembly
// 将r0,r1两个32位数存在r2指向的内存上的64数
strd r0, r1, [r2]
```

> On some ARMv7 processors, this instruction is not atomic. When the processor sees this instruction, it actually performs *two* separate 32-bit stores under the hood

## 原子性保证

原子写:

- When an atomic store is performed on a shared variable, no other thread can observe the modification half-complete,保证数据一次写完,防止其他线程读到半更新数据
- 常见于32位机器写64位数,只能分成2个MOV指令,破坏了原子性

原子读:

- 保证一次读完数据,防止在两次读的间隙数据又被更改

## 缺失危害

这种data race的后果: 

- 未提供原子写
  - 同时写: the upper 32 bits from one thread, the lower 32 bits from another.
  - 一读一写: any thread executing on a different core could read `sharedValue` at a moment when only half the change is visible,读到其他线程写了一半的数据
- 未提供原子读
  - 一读多写: 读到的数据类似于同时写,上4字节来自一个线程,下4字节来自另一个线程
  - 过程是: w1->r_hi32->w2->r_lo32

## 解决方法

对共享变量这种会产生多线程读写data race的情况(不同于普通的竞态,data race是如上所说,更底层的竞态)

因此,对于存在data race的共享变量,需要在__语言层面__提供__原子读写__,即对共享变量使用atomic rd/wr而不是plain rd/wr

对于现代体系架构,原子读写是默认支持的,除非你在32位机器上存储64位数,或是对共享atomic.Value的读写,这时,需要显式使用相关package的函数支持

> atomic.Value可能承载一个很大的结构体,比如sync.map里面,内置的built-in map是用atomic.Value实现的

> 在底层原子读写指令的实现,要么是锁cache line ,要么是锁总线(优先锁住cache行)

## CAS

cas的缺点: 可能会造成活锁和ABA问题

- 活锁: 虽然大家都在不断尝试,外界看起来也都在运行,但是没有一个人成功
- ABA问题: 这不是__CAS本身的问题__,而是在使用CAS时常见的错误用法
  - 因为使用CAS,你需要先加载旧值,oldVar = *addr,再CAS(addr,oldVar,newVar)
  - 再加载旧值和CAS之间,如果addr被人改了又改回去,你是无法识别的,这会导致newVar也许已经失效(如果是典型的链表场景)

> 如果要解决这个问题,可能需要加上版本号之类的

C++的`addr.compare_exchange_weak(oldVar,newVar)`当cmp失败时,会将oldVar置为新值,这可以很方便的让人写出CAS LOOP

```go
do{
	// do something about oldValue and get newValue
}
while (!shared.compare_exchange_weak(oldValue, newValue));
```

但是遗憾的是Go语言的`func CompareAndSwapInt32(addr *int32, old, new int32) (swapped bool)`	虽然提供了非侵入式的接口,但old值是不会改变的

## LL/SC

对于load-link/store-conditional指令,可以有效解决ABA问题

```go
oldVar = LL(addr)
// dosomthing
ok = SC(addr , newVar)
```

一旦在本线程LL后SC前,只要有其他线程访问了这个addr,就导致SC的false

## 锁

### Futex

fast userspace mutx

>  A futex consists of a [kernelspace](https://en.wikipedia.org/wiki/Kernel_(computing)) *wait queue* that is attached to an atomic integer in [userspace](https://en.wikipedia.org/wiki/Userspace).

查了很久,也没弄懂到底是个啥,如果按照上面这个wiki的定义,我倾向于说go的built-in mutex就是一种futex

```go
type Mutex struct {
	state int32
	sema  uint32
}
```

- state是位于用户态空间的,用于无竞态时的快速上锁

- sema则用于竞态时的阻塞

> 这样的锁也称为lightweight mutex [ref](https://preshing.com/20111124/always-use-a-lightweight-mutex/)



## 总结

### 竞态

- 宏观竞态race condition
  - 读写过程作为整体不原子,用RMW解决
- 微观竞态data race
  - 读写本身不原子,用原子读写解决

### 默认原子读写

it’s common knowledge that on all modern x86, x64, Itanium, SPARC, ARM and PowerPC processors, plain 32-bit integer assignment *is* atomic as long as the target variable is naturally aligned

### 处理器架构

处理器位数

- __386,i386(intel386),80386__ 都指intel的32位处理器

- __amd64,intel64,x86-64,x64__ 都指intel的64位处理器

处理器架构

- x86
  - __x86,x86-32,IA32__: x86是对Intel 8086、80186、80286、80386以及80486的架构的泛称,如今又称为x86-32,或IA-32
  - __amd64,intel64,x86-64,x64__: 由AMD公司所开发,基于IA32/x86-32架构

- IA64
  - IA-64: IA-64是一种崭新的系统，和x86架构完全没有相似性；不应该把它与x86-64/x64弄混

单独说x86,就是指x86-32/IA32/386/I386,单指32位intel处理器

如果是说x86-64,会说x64或amd64/intel64





