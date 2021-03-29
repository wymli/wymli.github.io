---
title: "kafka1 intro"
date: 2021-03-29
categories: ["mq" , "kafka"]
tag: ["mq" , "kafka"]
---

# kafka1 intro

> 部分参考
>
> 1. kafka技术内幕
> 2. https://zhuanlan.zhihu.com/p/68052232

kafka是一种流式数据处理平台(消息队列的进阶版,即除了完成的消息的转发外,还可以处理消息)

消息队列的三大功能: 

1. 异步
2. 解耦
3. 流量削峰

kafka作为流式数据处理平台的三大功能

1. 消息队列(消息系统)
2. 数据存储(容错,对等待转发的数据备份到持久化内存)
3. 实时流式处理数据

## 消息系统

两种常见模型

1. 点对点
2. 发布订阅topic

kafka使用消费组(consumer group)的概念,将其合并(消费组之间广播,消费组内部点对点)

> __注意__:  消费组是用于负载均衡的,指的是同一个消费组内的消费者是会接收到同一topic的不同消息的,即消息队列虽然会将消息广播给所有订阅它的消费组,但不会将消息广播给同一消费组的所有消费者,而是发送给消费组内的一个消费者(也就是负载均衡),至于发送给哪个消费者,与分区有关,详见后文

## 存储系统

如果收到的消息只是存在于内存中,那么断电后会造成消息丢失.因此,对于还未持久化的数据,不能认定为消息成功被消息队列接收.

为了保证可靠存储,消息生产者的生产请求应该是停等协议,必须收到消息队列已持久化消息的信息后(ACK),才认为生产成功. 因此生产过程是阻塞的.

## 流式处理

对于流式数据平台,仅仅有消息的发布订阅,持久化存储备份是不够的,还要有实时流式处理功能.

所谓流式处理,可以参照reactiveX这个库,它是一种类似于函数式编程里面常见的处理过程,比如映射,聚合,连接等等

在实际处理中,由于是网络通信,还可能面临乱序数据等问题

## API

kafka中有四个核心概念:

1. producer
2. consumer
3. connector,用于连接数据库,持久化备份,或者读取静态数据进行流处理
4. processor,进行流处理

# kafka实现: 基本概念

![preview](https://pic1.zhimg.com/v2-4692429e9184ed4a93911fa3a1361d28_720w.jpg?source=3af55fa1)

## 分区partition

kafka是一个分布式的消息队列,kafka集群由多个消息代理服务器(broker server)组成.

每个消息都有一个topic,表示消息的类别.每个topic会有多个订阅它的消费组,这个消费组会有多个消费者.当生产者发布消息后,所有的消费组都会收到消息,但是只会发送给消费组内的一个消费者.

kafka集群为每个topic都维护了一个分布式的分区日志文件(partition),物理意义上,主题可以看作分区的日志文件(partitioned log),这时因为生产者生产的消息会首先作为日志持久化到分区上(类似于redis的append-only file)(事实上,对于这种流式消息的持久化,也只能使用日志形式的追加).每个分区都是一个有序的,不可变的记录序列.分区中的每个消息都会按照到达的时间顺序被分配一个单调递增的偏移量offset,这个偏移量用于定位当前分区的一条消息(你可以想象成数组,偏移量就是下标)

> 当消费者来取消息时,由消费者自己维护消息消费的偏移量

在kafka的设计中,每个topic会有多个分区,每个分区唯一匹配该topic对应的各个消费组中的一个消费者. 不同分区之间的偏移量从0开始,独立互不影响.发布到topic的每条消息都包含key-value-timestamp,到达指定分区后都会被分配一个自增的偏移量,并持久化到分区日志文件.

> 每个topic的每个分区都会有副本存在,每个副本都独立位于不同的broker,并且其中一个副本是leader,其他的副本是follower
>
> 写数据只往leader写,然后主从更新,这是常见的读写分离优化. 往往,同一topic的不同partition的leader位于不同的机器上

因此,一般的,会将分区数设置为消费组内的消费者数,这样一个消费者唯一对应一个分区.如果以随机策略,那么生产者生产了该topic的消息,随机放在一个分区,然后消费组内与该分区对应的消费者去消费该分区,视为该消费组的消费.

当分区数与消费者数不等时,要满足一个分区只能对应一个消费者.即当分区数较多时,消费者可以对应多个分区,当分区数较少时,消费组内必然有消费者无对应分区

> 如果多个客户端都期望收到所有的消息,那么它们应该属于不同的消费组,并订阅该topic

### 消息有序性

只有单个分区内才保证消息的有序性,这是指消费该分区的消费者读取处理消息的顺序将总是和分区内的顺序是一致的

不同分区之间的消息有序性不保证,这是指某个消息虽然后到达某个分区,但却先被对应的消费者消费

如果想保证某些信息的强有序性,我们需要给该系列消息设置相同的键,使之映射到相同的分区. 或者更极端的,仅设置一个分区.

## 磁盘组织

partition就是一个一个的文件夹,每个partition的文件夹下面会有多个segment文件,每个segment文件包含三个文件

1. .index文件
2. .log文件
3. .timeindex文件

前面我们说了,message是以partition log的方式作为aof持久化的,所以消息其实存在.log文件中,,index文件和.timeindex文件是顾名思义的,都是索引文件

__TODO__: 具体的方式涉及持久化那章,目前还没找到完整的书,待更

## 生产模式

同一topic的不同partition之间是一层负载均衡,同一消费组的消费者之间也是一层负载均衡

对于生产者,它需要决定将消息写到对应topic的哪个分区,比如可以使用随机,轮询,平滑加权平均,一致性hash等手段(也就是rpc框架里的路由算法,也就是负载均衡算法). 当它确定了分区后,便去查询该分区对应的leader所属的broker,因为只有leader可写.

前面说过,生产者生产消息是一个阻塞的过程,需要收到消息队列(也就是broker)的ack. 实际上,有三种生产模式

按照如下图的工作流程:

1. 生产者可以在2后直接返回(完全异步)
2. 生产者可以在3后直接返回(阻塞,主持久化)
3. 生产者可以在6后直接返回(阻塞,主从同步持久化)

![img](https://pic1.zhimg.com/80/v2-b7e72e9c5b9971e89ec174a2c2201ed9_720w.jpg?source=3af55fa1)

## 消费模型

消息的消费模式有两种:

1. 推送push
2. 拉取pull

如果使用推送模式,则会增加broker消息代理服务器的负担,这是因为服务器应该为每个消息都记录消费状态,只要当收到消费者返回的ACK后,服务器才能有信心的将消息状态置为已消费,而在broker中,消息是大量的,维护这些状态的负担是较大的.此外,不同消费者消费的进度是不同的,需要额外存储各个消费者的进度.

简单来看,broker需要记录:

- 消息状态,是否已消费(比如,是否已被所有订阅的消费组消费)
- 不同消费者的消费进度(offset)
- 不同消费者的消费速率和broker的推送速率要对等

于是,Kafka采用拉取模型,有消费者自己记录消费状态,此时,消息是无状态的,broker不需要记录消息是否被处理过(但为了方便,其实还是会记录,这里只是说不记录也不影响主要功能).每个消费者独立且顺序的读取与自己相对应的那些分区的消息(典型情况下,分区与消费者是一对一的)

此时,由消费者自己维护的消息状态,其实是一个指针或偏移量offset,记录自己下一个要消费的位置.生产者最新写入的消息对消费者是不可见的,必须备份后才会更新watermark(最高水位),watermark存在的意义即是限制消费者的消费(颇有点len和cap的感觉).

简单来看,customer需要记录:

- 消费进度offset

> 这里的备份详见后文的副本与容灾,简单来说就是一个消息只有被所有从副本同步后(称为消息的提交),才能够被消费者看见从而消费,表现上就是watermark的增加

kafka不会像有些消息队列一样,当消息被所有消费组消费后,就立马删掉消息.而是会将生产者发布的所有消息保存在kafka集群,无论消费者是否已经消费.用户需要设置保留时间来清理过期数据.

这样的一个好处是,消费者可以通过更改自己的offset来消费以前的消息.(比如消费者逻辑出错,导致的回滚)

## 分布式模型

这里的分布式模型,也就是主从模型. 一个topic的不同partition在不同的broker上都将维护一个同样的副本.其中一个节点作为leader(主副本),其他节点作为follower(从副本).读写操作都只会打到leader上,当leader故障时,某个follower晋升为leader.

> 不是读写分离,而是读写都施加到leader上.
>
> 一个topic不同的partition在一台broker上,有的是leader,有的不是

### 分区路由

生产者需要自己决定将消息发送到哪个分区,然后再去寻找该分区的leader所在的broker的ip

当消息没有键时,将采用轮询的方式;当消息有键时,将通过某种手段将相同的键发到相同的分区(很显然,一种hash方法)

每个broker将会保存一份关于主题分区leader的metadata(元数据),这样就不需要一个统一的服务注册中心了. 生产者在生产消息之前,首先向任意一个broker申请元数据,以此确定每条消息的目的地

## 副本与容错

不同分区的主副本应该均匀地分配到各个服务器上,在主从同步上,从副本同步消息的过程和消费者消费消息的过程是一致的,只不过从副本会将消息写到自己的分区日志文件.

### 节点存活

节点存活必须满足两个条件:

1. 节点与zookeeper保持会话
2. 节点作为备份副本时,其备份进度不能落后主副本太多

此时,称其状态为in-sync,这些节点的集合为ISR(in-sync-replicas).

如果一个副本挂掉,没有响应或备份进度落后太多,那么主副本就会将其从ISR中移出,直到该从从副本赶上备份进度

### 消息提交

一个消息只有被ISR中的所有broker都持久化到本地的分区日志文件后,才被认为消息提交.只有消息被提交后,才能被消费者消费.如此而来,对消费者来说,消息是永不丢失的.

如果新生产的消息能立即被消费者看见,那么如果主副本宕机了,这些消息到底有没有被成功消费呢?如果没有,就需要生产者重新生产一份,这增加了很多额外的成本.不如直接设计成只有消息提交了才算生产成功

## 优化技术

### 零拷贝技术

显然,消息已经被持久化到了磁盘上,从磁盘上读取文件发送到消费者处,需要使用send_file,避免从内核态到用户态的拷贝与切换.

### 批量生产

在某些实时性要求不强(实际上,超时时间是极短)的任务中,生产者可以先尝试在内存中收集足够的数据,然后在一次请求中一次性发送一批消息(并会设置一个超时时间)

比如: 消息大小达到64B,就立刻发送,否则100ms后也立刻发送

### 批量消费

消费者理所当然的也可以一次接收一批数据,但是如果partition中消息数量不够呢?

消费者需要不断轮询broker(这时拉取式的缺点),解决方法是允许拉取请求是阻塞式,长轮询的,直到有足够的一批数据.



---

下一章: kafka2 生产者