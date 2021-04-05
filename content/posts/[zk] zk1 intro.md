---
title: "[zk] zk1 intro"
date: 2021-04-03
categories: ["zookeeper" ]
tags: [ "zookeeper"]
---

# Intro

> 官方文档： https://zookeeper.apache.org/doc/r3.4.14/

zookeeper是一种分布式协调服务(也就是说常称的注册中心),分布式应用正在运行的一组系统称为**集群**，而在集群中运行的每台机器被称为**节点**

服务器在整个集群中，有三种角色，分别是

- Leader
  - 处理写请求，事务调度和处理
- Follower
  - 处理读请求，转发写请求给leader，参与leader选举
- Observer
  - 同follower，但不参与leader选举

主从和主备

- 主从： 主节点分配调度任务，从节点执行任务
- 主备： 主节点作为日常工作节点，当主节点宕机后，备份节点成为主节点

实际上，我们使用的是主从和主备的结合，从节点不仅会执行任务，也会选举成为主节点

> 注意,采用主备模式的集群（比如kafka的某个主分区和备份分区），会有数据同步这个概念，即备份节点从主节点同步数据。
>
> 但是zk中，写是下发到从节点的，但它们的写提交是类似的，都要等大部分节点完成写/同步后，才算写的完成
>
> 这两者的区别，更像是主动和被动的区别，同步是从节点主动，而消息议案是主节点主动

## Guarantees

- Sequential Consistency - Updates from a client will be applied  in the order that they were sent.
- Atomicity - Updates either succeed or fail. No partial  results.
- Single System Image - A client will see the same view of the  service regardless of the server that it connects to.
- Reliability - Once an update has been applied, it will persist  from that time forward until a client overwrites the update.
- Timeliness - The clients view of the system is guaranteed to  be up-to-date within a certain time bound.

## APIS

zk 只支持7种操作，这里的node指的是znode

- *create* : creates a node at a location in the tree
- *delete* : deletes a node
- *exists* : tests if a node exists at a location
- *get data* : reads the data from a node
- *set data* : writes data to a node
- *get children* : retrieves a list of children of a node
- *sync* : waits for data to be propagated

## connection

Clients connect to a single ZooKeeper server. The client maintains a TCP connection through which it 

- sends requests, 
- gets responses, 
- gets watch  events, 
- sends heart beats. 

If the TCP connection to the server  breaks, the client will connect to a different server.

## znode

> znode： zookeeper data node

zk以类似目录的形式来组织数据，client要想找到想要的数据，需要先提供数据的路由地址（比如/app/1/p）, 和目录不同之处在于目录本身也能存数据，而不只是文件才能存数据

好像比较，其他的注册中心可能采用键值的形式，而不是路由的形式

> 小知识： gin的路由是基于radix数的

### znode结构

Znodes maintain a stat structure that includes version numbers for data  changes, ACL changes, and timestamps, to allow cache validations and  coordinated updates. 

Each time a znode's data changes, the version  number increases. For instance, whenever a client retrieves data it also receives the version of the data.

> ACL: Each node has an Access Control List (ACL) that restricts who can do what.

## 数据读

Read requests are serviced from the local replica of each server  database. 

Requests that change the state of the service, write requests, are processed by an agreement protocol.

## 数据写

As part of the agreement protocol all write requests from clients are forwarded to a single server, called the *leader*.

The rest of the ZooKeeper servers, called *followers*, receive message proposals from the leader and agree upon message delivery. 

> follower收到写请求->follower转发给leader->leader发送消息提案给follower->follower返回ack，表示接收消息写



## 数据更新

Updates are logged to disk for recoverability, and writes are serialized to disk before they are applied to the in-memory database.

> WAL : write ahead log,在写数据之前先写log，这里和数据库的区别是，数据是驻留在内存的，而log是在磁盘的

## 顺序

zab要求满足如下的顺序（都要满足）

- 全序（total order）
  - If message a is delivered before message b by one server, then every server that delivers a and b delivers a before b.
  - 这里的deliver message，可以理解为消息被client看见，即开始分发这个消息给client
- 因果序（causal order）
  - If message a causally precedes message b and both messages are delivered, then a must be ordered before b.

因果序有两种：

- If two messages,a and b, are sent by the same server and a is proposed before b,we say that a causally precedes b;
  - 由同一个server发送导致的消息顺序
- If a leader changes, any previously proposed messages causally precede messages proposed by the new leader.
  - 由leader变更导致的消息顺序

## 原子广播Zab

> ref： https://www.datadoghq.com/pdf/zab.totally-ordered-broadcast-protocol.2008.pdf

Zab协议下的服务有两种状态

- 广播
- 恢复

当一个新的服务开启，或leader宕机后，服务进入恢复状态，直到新的leader出现并且存在法定人数的follower与leader的状态同步，此后服务进入广播状态

对于服务器，也同样具有这两种状态，当一个新的服务器进入集群时，首先进入恢复状态，直到与leader同步，然后进入广播状态（当新server加入时，虽然它自己是恢复状态，但整个服务仍是广播状态）

### 写提交（write commit）

这是一种__两阶段提交__协议

> a leader proposes a request, collects votes, and finally commits

leader收到写请求后，将其作为消息议案（message proposal）广播给follower，follower在自己的in-memory database写这个消息后，返回ack给leader，当leader收到法定人数的ack后立马提交，而无需等待所有的follower的ack. 提交操作会广播commit消息给所有的follower，follower收到commit后，client就能从它那里读该消息了（当然，提交后client可以立即从leader那里读消息）

> 但是commit是没有ack的，如果leader自己commit后立马宕机了，follower都不知道这个消息commit了怎么办？

### 消息顺序性

Zab使用TCP协议，该协议本身就提供了一个FIFO通道（使用序号来排序），所以对端将会按发端发送的顺序接收消息

### zxid

每个被propose的消息都会被赋予一个单调递增的唯一id，称为zxid. 为了保证因果序，消息也会按照zxid进行排序

### 恢复

> a recovery procedure is necessary to elect a new leader and bring all servers to a correct state

两个原则：

- 当一个消息在一个服务器上可见（被commit），那么它就应该在所有服务器上可见
- 一个被跳过的消息应该维持其被跳过的状态
  - 否则就会违背消息顺序性

当leader收到来自法定人数的follower的commit后，该消息就在leader身上commit了，然后准备向follower广播这个commit，这时，leader宕机了，只有部分follower收到了这个commit

后续的leader被选举出来，follower首先会和leader同步状态，如果这个leader收到了那个消息的commit，那么其他follower应该提交这个消息，如果它没有收到，其他follower就应该取消对该消息的提交

在实现上，这是借助zxid实现的，zxid的低32位是递增的uid，高32位是与epoch相关的uid，没选举一次leader就会一轮

当上一次宕机的leader重新上线，它将作为follower，此时的leader将会检查follower的最进提交的消息的epoch，和自己的epoch里的最近提交的消息比对，并告诉follower删除那条提交

