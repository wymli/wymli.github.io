---
title: "[underTheHood] 基础-重要-知识-教旨-格言-蝉"
date: 2021-04-10
categories: ["underTheHood"]
tags: ["underTheHood"]
weight: 100
---


<!-- 
  hugo使用指南：
  hugo new posts/first.md
  hugo // 如果直接加文件，需要hugo一下，编译前端
  git add .
  git commit -m "asdf"
  git push
 -->

# UnderTheHood

这里记录一些具有重要的知识

## Page Cache

1. 主存充当两个功能,一个是进程的存储空间(堆栈),一个磁盘的缓存(page cache)

如此一来,一切都说得通了,我们常说read要从内核缓冲区拷贝到用户缓冲区,你也许和我有一样的疑惑,为什么要先拷贝到内核缓冲区呢?不能直接拷贝到用户缓冲区呢?

其实,这是属于名词的误用,这个内核缓冲区,其实不是缓冲区,而是磁盘的缓存page cache.当我们读取磁盘时,为了降低缺失率,我们会在内存中缓存磁盘的数据,这称为page cache.大部分未被分配给进程的内存都作为page cache存在.

因此,这里内核缓冲区到用户缓冲区的拷贝,实际是page cache到用户buffer的拷贝!

那为什么不直接从磁盘拷贝到用户缓冲区呢?

- 为了缓存

如果是直接拷贝到用户缓冲区,那么同时还要拷贝到page cache上,这是愚蠢的.就像cpu的cache一样,寄存器永远是从cache读数据,而不是从内存读数据,当cache缺失时,会read allocate,从内存拷贝到缓存,再从缓存拷贝到寄存器.这里也是一样的道理,从磁盘buffer拷贝到page cache,再从page cache拷贝到user buffer.(注意到磁盘也是有buffer,常称为disk buffer,是位于磁盘上的内存,用于减少io次数)

## 接受接口，返回结构

这是一个go谚语(或Gopherism),我们期望函数能接收抽象的类型,但是返回实际的类型.

接受接口,这是因为函数内部只需要调用有限的对象的方法,因此我们不期望限定死对象的类别,只要实现了对应的方法即可.

返回结构,这是因为接口定义了特定的有限的方法集,我们无法访问该结构其他的方法或内置变量,除非type assertion.这降低了用户的可操作性.

## 第三方库不应该panic,应该返回错误

## 进程，线程，协程
- 硬件线程：对硬件来说，四核八线程就是只支持8个硬件线程，即8条同时运行的指令序列。
- 内核线程：操作系统内核有专门的线程结构体task_struct，这个结构体就唯一代表了一个内核线程，内核可以调度内核线程运行到cpu的8个硬件线程上，典型的如pthread，对于该pthread执行的指令序列，可以视之为用户态的一个线程，因此典型的pthread是内核：用户=1：1。
- 用户态线程：完全由用户程序去调度异步的指令序列，一个异步的指令序列就可以看作是一个用户态线程，该线程需要的堆栈，调度都由用户态调度代码去完成，而不是内核来调度。 （堆是进程级别的内存资源不需要特别去管，因为是用户态，没办法去管理栈，只能访问堆，所以用户线程的栈是在堆上的，在堆上申请一下空间，在调度到这个线程的时候，就设置下cpu的esp，ebp寄存器的地址就好了。关于用户线程的栈还分共享栈和独立栈，栈是一种需要在堆上分配的资源，一种朴素的想法是每个用户线程都分配一个静态的一定大小的栈，称为独立栈，但这样会对资源浪费，因为很可能线程用不到那么大的栈空间；共享栈就是你线程运行时候的栈是一个公共的栈，大家所有线程运行的时候，ebp都是这个共享栈基质，当你被调度出去的时候，你就把你在共享栈上的数据保存到你自己的空间，调度回来的时候就把栈数据拷贝到共享栈重新运行。在实现上，可以多个用户线程共享一个栈，而不是所有用户线程共享一个栈，这样也许切换的不是和你一起共享栈的线程，你就不用拷贝栈，继续占着也可以）
  - 此时有两种模型
  - M:1，多个用户态线程跑到一个pthread上。
  - M:N，多个用户态线程跑到多个pthread上，简单来说就是可以跨内核线程调度，比如go的协程。

## 组件依赖
如果你只是想要实现一个差不多就行的，或者说是内部系统，建议不要引入太多外部依赖，可以使用一些嵌入式的数据库，比如badger，嵌入式kv。

## 原子读写
。。。

## protobuf
一个对象应该独立成一个message，而不是嵌入到Response。
```
// Contains Production-related information  
message Production {
  string id = 1;
  // ... more fields
}

message GetProductionRequest {
  string production_id = 1;
}

message GetProductionResponse {
  Production production = 1;
} 

service ProductionService {
  rpc GetProduction (GetProductionRequest) returns (GetProductionResponse);
}
```
一个良好实现上，Request应该加上FieldMask，以标识所期望收到的Response的字段，实现按需。http://dockone.io/article/2434655