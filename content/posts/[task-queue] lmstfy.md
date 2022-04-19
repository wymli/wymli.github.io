---
title: "[task-queue] lmstfy"
date: 2022-04-19
categories: ["task-queue"]
tags: ["task-queue"]
---

# lmstfy
碰巧github给我推了这个[任务队列](https://github.com/bitleak/lmstfy)，抽空读了下源码。如果第一次接触这种延时任务队列，还是挺有意思的。

## 架构
lmstfy使用redis作为底层存储，使用redis的list的`lpush`,`brpop`完成任务的生产和消费，消费要阻塞的pop，避免轮询。lmstfy使用redis设计了多个模块，ready队列是其一，还有timer zset的延时队列用来处理延时的任务，以及死信队列。  
假设称任务为task或job，下面统一称之为job。对于一个任务的提交（生产），它具有下面的生命周期：
1. 任务被加入任务池（redis kv实现），所有任务的body数据都以redis kv存储，而入queue入zset的都是任务的句柄或者说描述符或者说指针
2. 如果任务是延时的，加入延时队列（timer zset），对这个延时队列的操作以lua脚本的形式存在，简单来看就是按时间tick，将到期的任务句柄取出，判断是加入ready队列还是死信队列，判断依据就是任务的retry值是否为0
3. 如果任务是非延时的立即执行，则任务句柄直接加入ready队列，等待被`brpop`
4. 消费时，通过`brpop`取得任务句柄，随后从任务池中取回任务payload/body信息

对于一个任务被消费，它具有下面的生命周期：
1. 任务句柄存在于ready队列头部，被`pop`出来
2. 该任务句柄的retry数减一，并加入timer zset，防止客户端消费失败
3. 根据任务句柄从任务池中取出任务payload/body，返回给客户端

对于一个任务被确认或删除，它具有下面的生命周期：
1. 任务在任务池中被删除
2. 对于ready队列或延时队列（timer zset）中的任务句柄都不会被立刻删除
3. 对于ready队列，再次消费时会因为没有在任务池中取到任务而跳过（根据任务消费流程，该句柄仍然会retry减一并进入timer zset。也许可以先检查任务池之后再提交timer zset，不过源代码是这样写的，也无伤大雅）
4. 对于timer zset，再次tick时会检测到任务不存在于任务池而删除该句柄，从而该任务被彻底删除

对于延时队列，即timer zset，它具有下面的生命周期:
1. 客户端`preload` `lua`脚本到redis上
2. 客户端启动`NewTicker`，每个时钟滴答都调用redis上的lua脚本，分发过期的任务到死信队列或者ready队列
3. timer zset以`到期时间戳`作为score(`timestamp := time.Now().Unix() + int64(delaySecond)`)，这样只需要一个简单的`zrangebyscore 'zset_name' 0 time.Now()`就可以筛选出要到期执行的任务
4. 如果该任务句柄对应的任务不在任务池，说明已被删除，或任务池中的任务过期，反之无论如何，该任务丢失了
5. 如果任务池中存在该任务，查看任务句柄里的retry数
   1. 如果retry==0，则说明重试次数用完，加入死信队列
   2. 如果retry>0，说明还可以重试，加入ready队列
6. 在timer zset中删除刚才筛选出的到期执行的任务


一般来说，任务句柄包含几个字段：
1. namespace
2. queue
3. retry
4. jobID
前两个好理解，就是作用域，retry就是自动重试的剩余次数，jobID则用于在任务池中找到该任务。

## 对外API
lmstfy对外暴露的典型API是Publish，Consume，Delete，Peek，还有一些操作死信队列的API。  
> 其中Delete就是ACK的意思，一个客户端通过Consume消费任务队列后，应该调用Delete删除该任务


## Lua脚本
使用lua脚本的好处：如果采用Redis执行Lua脚本的方式实现多条指令，Lua脚本整体上在Redis中是原子的，并且在脚本执行期间，其他指令无法插入。并且Lua脚本编写简单，可以将一部分业务规则放入其中。而传统的与redis交互，即使是pipeline，也无法包含业务规则。
