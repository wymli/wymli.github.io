---
title: "[linux] server intro"
date: 2021-03-25
tags: ["server"]
categories: ["linux"]
---

# Introduction to linux server

linux 服务器导论

## 文件目录相关

假设我们的服务器名为testServerd,这里末尾以d结尾,代表daemon守护模式

> 如果是.d结尾,则代表是文件目录

### 日志目录

/var/log/testServerd/

> /var目录承载可变的数据文件,即可写,与之对比的是/usr,只可读

### PID记录

进程在创建时应该记录自己的pid,可以放置在

/var/run/testServerd.pid

### 配置文件

程序的配置文件可以放置在

/etc/testServerd/testServerd.conf

> etc是专用于放置配置文件的目录

## 用户信息

大部分服务器必须以root的身份启动,但不能以root的身份运行

### UID,EUID,GID,EGID

userid , effective userid, groupid,effective groupid

UID是进程的真实用户id

EUID是进程的有效用户id,是为了方便资源访问的,它使得运行程序的用户可以拥有该程序的有效用户的权限

> 如何设置有效用户? 一个可执行文件有一个set-user-id标志位,这个标志位表示普通用户运行程序时,有效用户就是该程序的所有者,使用chown改变程序所有者

### Switch User

调用`setgid()`和`setuid()`来切换由root身份启动的程序到普通用户身份



