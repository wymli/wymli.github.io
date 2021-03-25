---
title: "[linux] daemon"
date: 2021-03-25
tags: ["server"]
categories: ["linux"]
---

# [linux] 关于后台运行进程的小实验

我们经常有将进程放到后台运行的需求,我们可以通过编程实现守护模式,也可以在shell中启动进程的时候配置

## 守护模式

通过编程,可以使得程序进入daemon模式

> fork和setsid

## shell启动命令

1. &

使用&可以让进程后台运行,但是仍然会输出到终端上

```
setsid ./test.sh &
设置父进程为init进程
```