---
title: "[Interview] 杂"
date: 2021-03-25
tags: ["Interview"]
categories: ["Interview"]
---

# 记录一下为面试做的准备

> 声明: 以下知识点可能不完全正确,但也不会错的太离谱

记录一些知识点

1. 数据库事务的四个特性: ACID 原子性,一致性,隔离性,持久性
2. 事务的隔离级别: 
   1. 读未提交 : 即脏读
   2. 读提交: 解决脏读,可以读到其他事务提交了的行
   3. 读重复: 可以重复读数据,但是存在幻读(即对方插入了新的数据行,你是可以重复读出来行数不一样的)(要解决这个问题要锁全表)
   4. 读串化: 加表级锁
3. InnoDB的索引: B+树,有利于范围选择(对比hash和b树),B+树的数据指针节点都在叶子节点
4. 3层的B+树可以支持2kw数据索引(基于一页放一个结点,一页16KB,一行数据1KB)
5. 四,七层负载均衡: 
   1. 四层:传输层,根据(ip:port)来映射到不同的app server,其工作本质类似于一个NAT,它不查看包的内容
   2. 七层:应用层,以http为例,它可能会解析出http request line/header,根据url来映射到不同的app server
   3. 不管是哪种方式,连接都是client和proxy建立,proxy再与app server建立
6. 中断的分类:
   1. 外部中断: 外部io设备中断
   2. 内部中断
      1. 受迫中断: 除零等
      2. 自主中断: 系统调用
7. os是中断驱动的软件(指令序列)
8. 内核态与用户态切换的开销(系统调用的开销): 几百ns左右
   1. 特权模式的切换本身应该没有多耗时,主要是这个系统调用本身底层可能要执行数百条指令
   2. 对于getpid这样的系统调用,其实也是很快的,个位数ns左右
   3. 需要切换堆栈指针寄存器等
9. 进程上下文切换的开销(deprecated: see 16 instead)
   1. 进入内核态
   2. 切换页表寄存器指针
   3. 切换硬件寄存器上下文
   4. 执行调度代码(比如PCB进入运行队列)
   5. 冷启动造成的频繁缺页
10. 硬件线程上下文切换的开销
    1. 切换硬件寄存器上下文
    2. 内核态进行
11. 用户线程(协程)上下文切换的开销
    1. 用户态进行,超轻量
12. 线程比进程轻量的原因: 页表缓存
13. 协程比线程轻量的原因: 不用进入内核态
14. https: 7次握手(tcp3+tls4)
15. io复用: select和poll类似,需要自己去遍历整个event数组寻找哪些可读可写; epoll返回激活fd的数目fds,访问event数组的前fds个event即可
16. 进程切换的开销: [ref](https://www.youtube.com/watch?v=lS1GOdXFLJo)
    1. 直接开销: pcb的各字段的load&store(页表指针,界限指针等)(从内存到寄存器)
    2. 间接开销: cold cache
17. 内核线程切换的开销:
    1. 直接开销: pcb的各字段的load&store(页表指针,界限指针等)(从内存到寄存器)
    2. 线程和进程都是task_struct
18. 用户态线程的开销:
    1. 不需要进入内核态(进入内核态涉及中断)
19. 指令级并行: ILP 多发射,超标量(动态多发射)
    1. 多个取值译码器,多个ALU,单个执行上下文(所以只支持单进程的多发射乱序执行)
20. 线程级并行: 多核程序
    1. 单核多线程也可以,比如intel的四核八线程,在指令级并行的基础上增加多个执行上下文
21. 数据级并行: SIMD
    1. 单个取值译码器,超多个ALU
22. TLS握手:
    1. client hello,client random
    2. server hello,server random,server certificate
    3. client encode premaster secret using server public key
    4. <->通信双方根据预主密钥和random计算出对称密钥,用于后续通信的加密
    5. server->client ,  finished
23. 为什么要random: 避免重放攻击?
    1. 个人感觉不是,random就只是单纯的random一下,为了生成一个不易被爆破的密钥吧
    2. 为了避免重放,应该为每一个报文加一个序号
24. 为什么要对称密钥加密,而不是直接server公钥: 对称密钥加解密速度快
25. tcp三次握手,最后一次为什么要握手,没有行不行?
    1. 为了防止无意的过期连接的建立
    2. 可以类比有意的syn攻击(一种dos攻击)
       1. 防御手段? tcp cookie?
26. 数据库并发控制
    1. 悲观锁: 一次封锁或两阶段锁
       1. 一次封锁: 有效防止死锁,在事务开始时,一次获取所有锁,事务结束后释放所有锁
       2. 两阶段锁: 可能死锁, 事务分为growing阶段和shrinking阶段,前一个阶段只能获取锁,后一个阶段只能释放锁
          1. 解决死锁: 
             1. 死锁检测: 维护一个锁等待图,追踪每个事务要获得哪些锁,图中节点是事务,边是等待关系(i->j, 表示事务i等待事务j释放锁) ,系统周期性检查图中是否有环, 有环则死锁,对其中一个restart或者abort
             2. 死锁避免:  当事务i想要获取事务j的某个锁,dbms杀掉i或j来避免死锁
                1. old waits for young(wait-die)
                   1. 如果请求事务比持有事务启动的早,则请求事务wait; 否则请求事务abort
                2. young waits for old(wound-wait)
                   1. 如果请求事务比持有事务启动的早,则持有事务abort,释放锁; 否则等待
       3. 悲观锁的缺点: 大多数db读多于写,减少了潜在的并行性
       4. 意向锁: An intention lockallows a higher-level node to be locked in sharedor exclusivemode without having to check all descendent nodes.
          1. 如果表有意向读锁,则说明某一行加了读锁
          2. 如果表有意向写锁,则说明某一行加了写锁
          3. 意向锁与锁有一定的兼容性,本质是为了快速判断某一事物是否能在这个表上完成:
             1. <img src="C:\Users\salvare000\AppData\Roaming\Typora\typora-user-images\image-20210309091233223.png" alt="image-20210309091233223"  />
             2. 共享意向排他锁SIX: 表示读取整个表,修改部分行(即 S + IX),只有当某个事务是读取某一行时,才让其进入表(与之兼容)
    2. 乐观锁: 基于时间戳排序的协议(保证执行效果就像按时间戳串行一样)
       1. 不加锁,每个事务启动时获取一个唯一时间戳. 表的每一行都维护读时间戳和写时间戳
          1. 行的读写时间戳不能和事务启动时间戳矛盾
       2. 另一种方法,不在运行时验证,而是先写到自己的空间,事务提交时统一验证
          1. OCC phases(optimistic concurrency control)
             1. 读阶段,The DBMS copies every tuple that the txnaccesses from the shared database to its workspace ensure repeatable reads.
             2. 验证阶段: When txnTi invokes COMMIT, the DBMS checks if it conflicts with other txns.
             3. 写阶段:The DBMS propagates the changes in the txn’swrite set to the database and makes them visible to other txns
    3. 多版本并发控制
       1. 对于每一行,维护多个版本,只要一个事务写或修改了一行,就创建一个那一行的新版本(版本基于时间戳)
       2. 事务读时,会自己选择去读最新的与事务启动时间戳兼容的版本
27. 日志记录(持久化机制)
28. 高可用:  短暂的系统中断时间,能快速恢复(类比汽车的备胎)
29. 容错: 系统故障,但继续提供服务,因为冗余节点(类比飞机的多个发动机)
30. 灾备(disaster recovery): 系统故障后,如何抢救业务数据,放弃基础设施
31. 外排序: 以归并排序为例,对900MB数据排序,内存100MB
    1. 归并排序是divide-and-conquer算法,先分成多块,分别sort,然后对这排好序的多快进行merge
    2. 900/100 = 9,所有9路归并
    3. divide-sort阶段: 对这9块数据,每块100MB,依次读入内存,进行内排序sort,写出内存
    4. merge阶段: 内存分为9个input buffer和1个output buffer;每次对每块读入10MB,进行merge,output buffer满后写出内存,input buffer满后,从自己那块再从磁盘取
32. redis持久化机制:
    1.  RDB:redis database
       1. 将数据快照保存在磁盘上
       2. 命令: save(同步save) , bgsave(异步save),自动同步(配置文件)
       3. 缺点: 自动同步时间一般设置的较大,比如100s,实时性不够
          1. 显然不能频繁写,因为要把内存全部覆盖到磁盘,数据量还是很大的
    2. AOF: append-only-file
       1. 存储日志,恢复时redo,可以配置每一条指令,或每秒fsync一次
       2. 缺点:aof文件比rdb文件大
       3. 优点: append-only,方便磁盘寻址
       4. bgrewriteaof,对aof文件重写(优化),目的是为了减少指令数目,用尽可能少的指令数目完成一样的功能; 有助于数据恢复速度和磁盘空间
33. WAL: write ahead log
    1. 先写日志再写数据
