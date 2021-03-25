---
title: "[rpc] rpcx"
date: 2021-03-25
tags: ["rpc"]
categories: ["rpc"]
---

# RPC识记-微服务概述

respect： rpc框架:  https://doc.rpcx.io/

## 关键字

服务发现，注册中心，服务治理，限流熔断隔离降级，codec等

## Outline

- 一般的，一个rpc框架就是一个微服务框架
- 一个好的协议,request和response应该是同样的格式
- 插件化与回调
- 服务发现
  - 点对点
  - 注册中心
- 服务选择
  - 重试策略
  - 节点选择策略

- 限流熔断，隔离降级
- 编解码codec
  - 不同的序列化手段
- 服务监控
  - trace：调用链追踪
  - logging：日志
  - metric：指标，统计分析

## 服务发现

- 服务发现

  - 类似DNS，是一个kv数据库，完成servicName到ip:port的映射

  - 点对点

    - 直接指定对端ip:port，dial对端，不需要服务发现

  - 点对多

    - 同点对点，但指定了多个对端ip：port,它们将提供同样的服务，客户端在此模式下可以有不同的重试策略。

  - 注册中心： zookeeper ， etcd ， consul

    - 服务注册中心用来实现服务发现和服务的元数据存储（比如serviceName到多个ip:port的映射）。

    - 传统的服务发现可能直接由静态配置文件设置，并且可以运行时动态监听文件修改并重新读入并应用。

    - 更现代的方式是拥有一个注册中心，我们不再维护本地的配置文件，好处是注册中心是中心化管理，多个客户端共享。

    - 注册中心都实现了某种分布式共识算法（指注册中心本身是分布式的（比如一个部署好的zookeeper集群），保证其某个节点失效仍可正常运行),其本质就是一个分布式键值数据库，如etcd

    - 此模式下，使用rpc时，不再需要指定服务主机地址，而替换为注册中心集群地址

    - 一般的，客户端将会向注册中心订阅，这样服务的动态变化将会异步通知到客户端。而不是客户端每次请求都去访问注册中心

      

      

> dubbo架构：<img src="https://user-gold-cdn.xitu.io/2020/4/5/1714936be64477c3?imageslim" alt="img" style="zoom:30%;" >

## 服务选择

服务选择：

- 失败模式（重试模式）：当遇到超时或网络错误，该怎么办？
  - 直接失败
  - 重试其他节点
  - 重试当前节点
  - 广播一定数量的目标节点，有一个成功就算成功
- 节点选择
  - 随机
  - roundrobin（顺序调用）
  - weightedRoundRobin（在一个周期内，权值高的调用次数多，且较均匀的分布在周期内）
    - 本质也是生成一个调用队列，依次出队
  - 网络质量优先（基于ICMP ping）
    - 也要防止网络状态不好的服务主机一直饥饿
  - 一致性哈希
    - 指满足均衡性，单调性，分散性，低负载的哈希算法，该算法将hash值空间组织成虚拟的环
    - 首先将服务主机的ip:port计算出哈希值，store进哈希表
    - 然后客户端对serviceName:serviceMethod:args计算出哈希值，将该值在环上按一定方向移动，第一个遇到的主机就是选中的主机
  - 地理位置优先（计算经纬度）
  - 自定义

## 限流熔断，隔离降级

- 限流：rateLimit

  - 目的：有损服务，而不是不服务

  - 限流对象

    - TCP连接请求
      - 一般无法限制tcp的建立，除非中间加一层代理网关
    - QPS：连接建立后，是否被处理

  - 限流处理

    - 返回错误码，比如http常见的500 internal error
    - 服务端阻塞等待一段时间，看能否在超时时间内被处理

  - 常见算法：

    - 固定窗口计数器

      - 比如每分钟为一个窗口（一般以整分钟开始1分钟到2分钟一个窗口），限制每个窗口内最多1000个连接
      - 缺点：对于随机选取的时间长度为1分钟的区间（比如1.5分钟到2.5分钟），不一定满足连接数小于1000

    - 滑动窗口计数器

      - 固定窗口相当于长度为1的滑动窗口
      - 比如以每秒钟为一个窗口，设置滑动窗口的长度为60，要求每分钟最多1000个连接。
      - 每过1秒钟，滑动窗口向前移动一个小窗口，每个小窗口将维护一个计数，记录这个小窗口的时间期间到来的连接数
      - 新的连接能否在新的小的时间窗口内被接收，取决于的逻辑的长度为60的滑动窗口内的所有小窗口记录的连接数之和是否大于1000

    - 令牌桶 token bucket

      - 维护一个有大小的令牌桶，若桶未满，则以一定的速率生成令牌放入桶中

      - 每个请求必须在申请到令牌后，才会被处理，否则限流

      - 原生令牌桶是基于字节数判断一个packet是否有效，即限制的是读写的byte数

        - 详见https://en.wikipedia.org/wiki/Token_bucket

        - 一个限流器实现： https://github.com/juju/ratelimit,   其reader/writer实现:

          - ```go
            func (r *reader) Read(buf []byte) (int, error) {
            	n, err := r.r.Read(buf)
            	if n <= 0 {
            		return n, err
            	}
            	r.bucket.Wait(int64(n))
            	return n, err
            }
            
            func (w *writer) Write(buf []byte) (int, error) {
            	w.bucket.Wait(int64(len(buf)))
            	return w.w.Write(buf)
            }
            ```

      - 实际上也可以用于直接限制连接：

        - ```go
          // rpcx的限流插件：实现了PostConnAcceptPlugin接口
          //	PostConnAcceptPlugin interface {
          //		HandleConnAccept(net.Conn) (net.Conn, bool)
          //	}
          func (plugin *RateLimitingPlugin) HandleConnAccept(conn net.Conn) (net.Conn, bool) {
          	return conn, plugin.bucket.TakeAvailable(1) > 0
          }
          ```

    - 漏桶

      - 维持一个固定大小的连接队列，以恒定的速率出队

- 熔断： circuit breaker（断路器）

  - 熔断属于服务作为客户端时的行为
  - 当对一个节点的调用出现连续的错误时，断路器将打开，后续对该节点的调用将直接返回错误。一定时间后断路器半开，允许一定数量的请求，若正常访问则全开，否则继续断开
  - 这主要是为了防止大量的请求处于请求发出而未超时的等待阶段，若这个客户端本身作为服务，则也会影响自身的服务提供，导致雪崩
    - 因为资源是有限的，一个goroutine要2k的栈，再加上1k的recv buffer等等

- 降级

  - 服务降级：本质就是提供有损服务
  - 限流和熔断都属于服务降级

- 隔离

  - 将本机的各个服务隔离开，这也是docker这类容器的优点：隔离
  - 实现上，就是对资源的获取是有限度的，比如设置最大的goroutine数，这可以通过线程池做到

## 编解码codec

常见的编解码器，即对对象的序列化和反序列化功能

- binary
- json
  - 对性能要求不高的场景，可读性高
- protobuf
  - google出品
- messagePack



![data:image/png;base64,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](C:\Users\salvare000\Desktop\翻译\4fZMeqakt94xkAAAAASUVORK5CYII=.png)

## 插件化和回调

rpcx提供了多种回调接口,只要插件实现了这些接口，再注册进插件中心即可在合适的地方被调用

比如限流插件，我们期望其在连接建立后被调用，因此要实现`HandleConnAccept(conn net.Conn) (net.Conn, bool)`方法

```go
type (
	// ... 省略一部分

	// PostConnAcceptPlugin represents connection accept plugin.
	// if returns false, it means subsequent IPostConnAcceptPlugins should not continue to handle this conn
	// and this conn has been closed.
	PostConnAcceptPlugin interface {
		HandleConnAccept(net.Conn) (net.Conn, bool)
	}

	// PostConnClosePlugin represents client connection close plugin.
	PostConnClosePlugin interface {
		HandleConnClose(net.Conn) bool
	}

	// PreReadRequestPlugin represents .
	PreReadRequestPlugin interface {
		PreReadRequest(ctx context.Context) error
	}

	// PostReadRequestPlugin represents .
	PostReadRequestPlugin interface {
		PostReadRequest(ctx context.Context, r *protocol.Message, e error) error
	}
	
    // ...省略一部分
)
```

插件中心将会在合适的地方调用注册好的插件，比如read前后的回调：

```go
func (s *Server) readRequest(ctx context.Context, r io.Reader) (req *protocol.Message, err error) {
    // here callback
	err = s.Plugins.DoPreReadRequest(ctx)
	if err != nil {
		return nil, err
	}
	// pool req?
	req = protocol.GetPooledMsg()
	err = req.Decode(r)
	if err == io.EOF {
		return req, err
	}
    // here callback
	perr := s.Plugins.DoPostReadRequest(ctx, req, err)
	if err == nil {
		err = perr
	}
	return req, err
}
```

一个朴素的插件中心的实现,将会把不同的插件无差别的放进一个[]interface{}，调用时再遍历一个个type assertion，看是否是想要的接口，这也是rpcx默认的插件中心的实现方法

```go
//DoPostConnAccept handles accepted conn
func (p *pluginContainer) DoPostConnAccept(conn net.Conn) (net.Conn, bool) {
	var flag bool
	for i := range p.plugins {
		if plugin, ok := p.plugins[i].(PostConnAcceptPlugin); ok {
			conn, flag = plugin.HandleConnAccept(conn)
			if !flag { //interrupt
				conn.Close()
				return conn, false
			}
		}
	}
	return conn, true
}
```



## 下一代微服务

service mesh

- 分为数据面和控制面，用户只需编写数据面即可