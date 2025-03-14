---
title: "[Go] mutex"
date: 2021-03-25
tags: ["Golang"]
categories: ["Golang"]
---

# mutex
## 结构
```go
type Mutex struct {
    state int32
    sema  uint32
}
```
自旋
```go
for{
  cas(m.state)
}
```
阻塞
```go
wait(m.sema)
```
## 状态
- 普通模式
  - 就是正常的模式,线程相互竞争获得锁
- 饥饿模式
  - 由于线程竞争失败会阻塞,而这些被唤醒的线程会和其他第一次来申请锁的线程一起竞争,显然,不可能竞争过,因为新的线程是占据着cpu的
  - 这会导致阻塞线程的饥饿,因此,mutex加入了饥饿模式,当进入饥饿模式后,锁直接赋予阻塞队列的第一个线程,新线程自动加入阻塞队列

> 注意,对锁的竞争,有两大来源,一是新线程,二是被阻塞线程(由于锁的释放而被唤醒),新线程如果自旋一段时间后未获得锁,便进入阻塞态,加入该锁的等待队列

### 加锁
Lock 对申请锁的情况分为三种：
- 无冲突，通过 CAS 操作把当前状态设置为加锁状态
- 有冲突，开始自旋轮询，并等待锁释放，如果其他 goroutine 在这段时间内释放该锁，直接获得该锁；如果没有释放则为下一种情况
- 有冲突，且已经过了自旋阶段，通过调用 semrelease 让 goroutine 进入等待状态
> 摘自 https://golang.design/under-the-hood/zh-cn/part4lib/ch15sync/mutex/

> goroutine会自旋轮询四次,如果失败,就在信号量上阻塞睡眠

### FSM
- 进入饥饿模式
  - 如果一个 goroutine 等待 mutex 释放的时间超过 __1ms__，它就会将 mutex 切换到饥饿模式
- 退出饥饿模式
  - 它是等待队列中的最后一个
  - 它等待的时间少于 1ms