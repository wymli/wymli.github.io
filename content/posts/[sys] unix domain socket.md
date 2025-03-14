---
title: "[sys] unix domain socket"
date: "2021-03-28"
categories: ["sys"]
tags: ["sys","socket"]
---

荐读 [unix domain sockets vs. internet sockets](https://lists.freebsd.org/pipermail/freebsd-performance/2005-February/001143.html)

简单说来,就是internet socket(使用AF_INET地址族),即使是dial本机localhost来通信,其也会经历一个完整的网络流程(虽然是通过lo网卡),也会收到syn,ack包,只是碰巧在解析的过程中,机器发现了这个包是要路由到本机的,于是借助lo网卡回来,本质仍然是一种尽力交付

但是unix domain socket不同,它是专用于做本机ipc的,是一种可信交付,它直接将数据写到recv socket 的buffer,而不需要header,checksum这些东西



