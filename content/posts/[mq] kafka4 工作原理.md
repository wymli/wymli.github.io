---
title: "[mq] kafka4 工作原理"
date: 2021-04-03
categories: ["mq" ]
tags: ["mq" , "kafka"]
---

# 深入kafka

在此前的系列中,其实对于kafka集群和zk集群的区分很模糊,数据似乎有时是存在某个broker中的,又有时是存在zk中的

## kafka成员

kafka使用zk来维护集群成员的信息.