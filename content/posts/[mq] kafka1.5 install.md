---
title: "[mq] kafka1.5 install"
date: 2021-04-01
categories: ["mq"]
tags: ["mq" , "kafka"]
---

# 安装kafka

我们知道apt-get install只能安装某个版本的软件,这取决于在软件源那里的最新软件版本,你可以使用apt-get search搜索看有没有自己想要的版本

一般的,为了安装特定的版本,或自己没有root权限,我们需要自己手动下载安装包编译,或解压

[TOC]



# 安装zookeeper

首先安装zk

## 解压

对于.tar.gz格式的压缩包,使用`tar -zxvf `轻松解压

对于.zip格式的压缩包,需要使用unzip

## 默认安装目录

一般的,程序会被安装到`/usr/local/`

所以我们执行如下的命令:

```sh
tar -zxf zookeeper-3.4.6.tar.gz
mv zookeeper-3.4.6 /usr/local/zookeeper 
```

usr目录,也许可以理解成user shared resource,总之就是只读资源目录的意思

- 如果是配置文件,一般放在/etc目录
  - editable text configuration

- 如果是日志文件或数据文件,一般放在/var目录
  - variable,可变数据,即需要常更新写入的日志

## 创建配置

可以使用__here document__的用法,即使用`cat > file << EOF`来在终端写入一个多行文本

```sh
cat > /usr/local/zookeeper/conf/zoo.cfg << EOF 
> tickTime=2000 
> dataDir=/var/lib/zookeeper 
> clientPort=2181 
> EOF
```

### 配置说明

zookeeper是一个分布式数据库,基于某种一致性协议进行节点同步

当节点个数有一半不可提供服务时,zookeeper就不对外提供服务(即如果有多数节点能提供服务,zookeeper就能提供服务)

- 因此,一般建议配置奇数个节点,比如3个节点,则允许坏1台;5个节点,允许坏2台;一般不建议大于7,因为会增加一致性协议同步的负担

### TickTime

服务器会主动的轮询自身集群的状态,这个间隔就是ticktime,一切的其他与时间有关的任务,比如从节点与主节点最大的不同步时间,比如从节点和主节点初始化连接的超时时间

这样好处是,在底层实现上,我们的确是以一定的时间间隔来轮询的.

### 通信端口与选举端口

对内,zk集群内节点会暴露两个端口,一个是用于通信的端口,一个是用于leader选举的端口

对外,整个zk暴露一个clientPort,用于客户端的连接

### Paxos&ZAB协议

paxos是Lesile Lamport于1990年提出的基于消息传递且具有高容错特性的一致性算法

zookeeper的一致性算法并没有完全采用paxos,而是使用了一种称为zookeeper atomic broadcast(ZAB,zookeeper原子消息广播协议)

Paxos是通用算法,ZAB是非通用的专用于zk的一致性算法

### leader&follower&observer

在zookeeper中,节点有三种类型:

- leader
- follower
- observer

其中,leader和follower称为公民,用于计算存活节点;follower和observer称为learner.

leader只有一个,为客户端和follower提供读写服务.leader也可以拒绝客户端的连接,而只向follower提供写服务.

follower只提供读服务,对于写请求,会统一转发到leader,由leader进行统一的调度

对于写操作,leader接收到来自follower的写请求后,向所有follower转发写请求,当有过半follower返回ack后,则在leader服务器上提交写请求,代表写成功. 对于那些在leader提出但未提交的写事务,则会被丢弃

以上只是简略的一个介绍,其目的是知道这些名词,详细介绍应该去看书,或者zk系列文章

> 注意zookeeper需要设置三个端口,分别用于接收客户端请求clientPort,节点间通信peerPort和节点间选举leaderPort.

# 安装Broker

解压后移动到/usr/local即可(因为/usr/local是在path的)

当然,kafka还要求设置log目录和JAVA_HOME环境变量

```sh
tar -zxf kafka_2.11-0.9.0.1.tgz
mv kafka_2.11-0.9.0.1 /usr/local/kafka
mkdir /tmp/kafka-logs
export JAVA_HOME=/usr/java/jdk1.8.0_51
```

启动脚本启动服务器:

```sh
/usr/local/kafka/bin/kafka-server-start.sh -daemon
/usr/local/kafka/config/server.properties
```

创建topic并打印信息

- `replication-factor=1` 表示复制因子为1,即每个partition只有一个副本(这个副本,不是指额外的拷贝,而是算自身的,所以如果你想一个leader,一个follower,则应该设置复制因子为2)

- `--zookeeper localhost:2181` 首先连接到zk,然后指定主题名`--topic test`,然后指定动作:`create`或`describe`

```sh
/usr/local/kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --create 
--topic test --replication-factor 1 --partitions 1 
> Created topic "test".
/usr/local/kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --describe 
--topic test

```

生产者向对应topci生产消息

- 这里`Test Message 1\nTest Message 2`是自己的输入,使用ctrl-D输入EOF
- 这里:9092是kafka默认监听的端口,因此生产者其实不需要指定zk

```sh
/usr/local/kafka/bin/kafka-console-producer.sh --broker-list
localhost:9092 --topic test
Test Message 1
Test Message 2
^D
```

消费者从对应topic消费消息

```sh
/usr/local/kafka/bin/kafka-console-consumer.sh --zookeeper
localhost:2181 --topic test --from-beginning
Test Message 1
Test Message 2
^C
Consumed 2 messages
```



很奇怪,为什么一会是连接zk,一会是连接kafka呢?

