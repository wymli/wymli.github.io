---
title: "[Interview] ByteDance2"
date: 2021-03-27
tags: ["Interview", "ByteDance"]
categories: ["Interview","ByteDance"]
---

# 字节二面

1. 算法题: 二叉树中的最长距离
   1. 又拉跨了,太久没做题了,做了很久
2. 并发和并行的区别
3. 讲讲go的协程调度
   1. GMP模型,balabala讲一堆,提到了netpoller,触发linux io复用剧情
   2. 讲到了steal机制,面试官问我为什么在全局队列未空的时候要去steal呢?
      1. 回答,应该不会吧,毕竟其他p的g可能不在一个核上,会增加cahce缺失率
4. 讲讲linux的io复用
   1. select/poll/epoll
5. select和epoll的区别
   1. 说了些常见的,比如select用链表不限制fd个数,但是触发后要遍历所有fd,epoll只需要遍历已经激活的fd,数组的前n个
   2. 似乎不是面试官想要的,让我回去再看看
6. 提到epoll只返回激活的fd的个数,问我怎么设计这个数据结构
   1. 其实没搞懂想问什么,于是我balabal扯了一堆
7. 讲讲docker
   1. 一种linux容器
   2. 虚拟化,轻量级,隔离
   3. dockerfile可以很方便的构建容器镜像
8. 讲讲TCP的分包
   1. tcp是面向流的协议
   2. 基于长度
   3. 基于分隔符
9. 分隔符和内容冲突了怎么办?
   1. 转义
      1. 这里可以参考http协议,使用\r\n来分隔,对于body,会使用base64编码转义成文本字符,header和body之间有两个\r\n来区分
   2. 配对
      1. 比如json,xml这种,但显然面临注入的风险,也要转义
   3. 定长
      1. 对于简单的报文,直接定长即可
10. 看我实验室的经历,问我知道哪些机器学习算法
    1. 讲了些简单的
11. 怎么对垃圾邮件分类
    1. 首先肯定是要特征工程,将邮件编码为欧氏空间中的一个点(向量,embedding),然后就是加标签之类的,丢到算法里面fit参数,我只懂些皮毛
12. 问我svm怎么分类
    1. 没搞懂要问什么,以为要讲原理,我说一个分类间隔,支持向量啥啥啥的,反正我不懂,瞎扯一堆
    2. 最后说只需要怎么使用
       1. 那不是直接丢进去fit参数就行了嘛,重点在特征工程,分词那些吧,没搞懂面试官的逻辑
13. 其他,忘了,暂时只想起来这么多