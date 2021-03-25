---
title: "[rpc] grpc"
date: 2021-03-25
tags: ["rpc"]
categories: ["rpc"]
---

# GRPC

创建一个rpc连接,需要三端努力,即客户端,IDL,服务端

> IDL: interface define language

但是似乎其他的rpc框架,并没有执着于使用IDL来定义接口,而直接在代码中使用字符串来指示远程过程函数名