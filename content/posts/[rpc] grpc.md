---
title: "[rpc] grpc"
date: 2021-03-27
tags: ["rpc"]
categories: ["rpc"]
---

# grpc

grpc是一种rpc框架,先不管其实现或特点.首先我们明确,不管是什么rpc框架,其最终目标都是让用户能够在应用层轻松的调用远程的函数,就像在本机上调用一样.

如果你还不知道这个,请移步另一个文章[rpc] intro,以及[rpc] net-rpc



gRPC是Google公司基于Protobuf开发的跨语言的开源RPC框架。gRPC基于HTTP/2协议设计，可以基于一个HTTP/2链接提供多个服务，对于移动设备更加友好

## desc

很明显了,grpc使用protobuf作为序列化协议,基于http/2作为通信协议