---
title: "[DB] redis"
date: 2021-07-03
tags: ["Database", "redis"]
categories: ["Database","redis"]
---

# 关于redis的大部分事情

1. 非常不错: https://redis.io/topics/data-types-intro
2. redis的数据结构:
   - Binary-safe strings.
   - Lists: collections of string elements sorted according to the order of insertion. They are basically *linked lists*.
   - Sets: collections of unique, unsorted string elements.
   - Sorted sets, similar to Sets but where every string element is associated to a            floating number value, called *score*. The elements are always taken sorted by their score, so unlike Sets it is possible to retrieve a range of elements (for example you may ask: give me the top 10, or the bottom 10).
   - Hashes, which are maps composed of fields associated with values. Both the field and the value are strings. This is very similar to Ruby or Python hashes.
   - Bit arrays (or simply bitmaps): it is possible, using special commands, to  handle String values like an array of bits: you can set and clear individual bits, count all the bits set to 1, find the first set or unset bit, and so forth.
   - HyperLogLogs: this is a probabilistic data structure which is used in order to estimate the cardinality of a set. Don't be scared, it is simpler than it seems... See later in the HyperLogLog section of this tutorial.
   - Streams: append-only collections of map-like entries that provide an abstract log data type. They are covered in depth in the [Introduction to Redis Streams](https://redis.io/topics/streams-intro).
3. hyperloglog计数(计算集合大小)的误差 less than 1% ,  最多 12KB的空间
4. redis的value最多512MB, 但是经验表明100MB就比较慢了
5. redis server-assisted client side caching
   1. 很明显,我们有时候要在机器上做localcache,比如常见的bigcache
   2. 如何保证本地缓存和redis数据的一致性是一个问题
      1. 简单场景,对实时性要求不高,给本地缓存设置一个过期时间即可
      2. 复杂场景,使用redis的pub/sub系统来发送失效消息(类似基于失效的缓存一致性模型)
         1. 但是这个发大了太多倍写流量,对每个写,都要发失效消息给每个订阅的client,但很可能那个client其实没有缓存该数据
      3. redis实现:
         1. tracking模式: redis存储客户端请求过哪些key,当这个key变动时,发送失效消息给客户端; `客户端需要显式传送CLIENT TRACKING ON指令来开启tracking`
            1. 实际上server维护了固定大小的全局一张表,当满时,淘汰旧的key,发送invalid消息,这造成了不必要的流量,但有限减少了server的内存开销
         2. broadcasting模式: 客户端决定订阅哪些前缀,server维护一个前缀表,当某个key被修改,server则发往所有订阅了该前缀的client invalid消息,而不管client是否之前read了这个key
6. redis cluster
   1.  主从读写分离, 写只由master写,读均摊到各个slave?
7. redis 附加组件module
   1. 比如RedisBloom - Probabilistic Datatypes Module for Redis, 提供了布隆过滤器,topk等数据结构用于大数据流处理
   2. 使用: 在redis.conf中的loadmodule字段配置 /${dir}/redisbloom.so , 该.so的获得一般是通过clone 源代码,然后make