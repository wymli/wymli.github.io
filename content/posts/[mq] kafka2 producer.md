---
title: "[mq] kafka2 producer"
date: 2021-03-31
categories: ["mq"]
tags: ["mq" , "kafka"]
---

# kafka producer

> 参考kafka技术内幕:图文详解kafka源码设计和实现

本节主要讲关于kafka的生产者相关的事情,比如同步与异步的api调用,底层的网络通信框架(比如rpc)

## 回顾

在kafka1 intro中,我们知道了典型的kafka架构,我们有producer,broker,consumer,connector(目前我们对connecter还基本没有什么了解)

broker就是所谓的消息中心,它是分布式的,并且是partition相关的分布式.

一个topic有多个partition,每个partition仅与一个消费组中的消费者关联,topic将会在多个broker中存在,作为备份,那么就会有主从之分,但是主从区分的粒度不是topic,而是partition.这样可以保证broker的负载均衡,因为消费者只会读写主partition,从partition将会作为另类的消费者去读写主partition来同步.

## 同步与异步api

同步api将会造成阻塞,而异步api立即返回.

这里我们主要关注设计,异步api需要传入回调函数,用于在broker返回ack后执行,显然,这需要新开一个线程,监视网络入包.

无论是同步还是异步api,其下一层应该都调用同样api,事实上,kafka的producer.send()方法会返回一个future,如果调用future.get(),那么自然阻塞.

> 注意异步api要设计 传入回调函数 

## 分区路由

对于给定key的消息,我们先对key散列,然后对分区数取模,这样就能保证同一个key的消息能发送到同一个partition

对于未指定key的消息,我们采用轮询partition的方法

> 这里的轮询指round-robin,也就是顺序循环,说成轮询其实不太好

> 显然还可以有更多的路由算法,比如如果分区数与消费者数不匹配,那么显然有一些分区的负担低一点,这时候可以更多的往该分区发送消息(基于加权的路由,可以参考nginx的加权平滑路由算法)

为什么要增加分区路由,而不增加一个负载均衡器,producer将信息发往负载均衡器,然后由负载均衡器进行消息的路由呢?

主要是这因为: 

1. 一台负载均衡器负责所有producer的转发路由,负担较重
2. 从producer到load balancer,再从load balancer到broker,是位于一个网络中的,于是造成了两倍的网络开销

## 消息缓冲

kafka设计了消息缓冲器RecordAccumulater,当producer调用send方法后,首先会向accumulater追加消息,如果收集器满了,就唤醒sender线程,异步发送消息

记录(消息)是按批发送的,目的也是为了减少io次数,网络开销

在kafka的设计中,accumulater是一个双端链表,每个链表节点是一个固定长度的数组,代表一批. 显然,有多少个分区,就有多少个链表.

## 发送线程

一种朴素的方法就是迭代accumulater的所有链表,直接往分区的主副结点发送.

另一种较高效的方法是先将分区按其主副结点分组(即不同的分区的leader可能在同一个broker),那么这时候将这两个分区打包发送,又减少了网络开销

> 我想到的一种方式就是accumulater维护一个map<brokerId , [ ]accumulater_partition>,记录节点到分区的映射,sender线程只需要遍历这个map,即可完成对partition的分组

在kafka的设计中,sender线程并不真正发送数据,这是因为网络连接需要更多的封装和抽象,sender线程仅准备好一次连接发送的所有数据

## 网络连接

NetworkClient对象提供了对客户端和服务端之间通信的封装,包括连接建立,发送请求,读取响应等.

为了保障服务器性能,在网络连接对象中,我们限制了对同一broker的连接数为1,即当上一次send还未收到ack时,这次的对同一broker的connect将会被禁止

> 从源码阅读上看,清晰度完全不如go啊

