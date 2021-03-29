---
title: "[DB] mutex"
date: 2021-03-25
tags: ["DB"]
categories: ["DB" , "innoDB"]
---
# 数据库中的三种锁

[ref](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-record-locks)

1. record锁(行锁)
2. gap锁(间隙锁)(左开右开)
3. next-lock锁(行+间隙)(左开右闭)

注意,锁的区间不是任意的,是依托于索引的键的.相当于说锁和非叶子节点的指针一对一的

> A record lock is a lock on an index record. For example,        `SELECT c1 FROM t WHERE c1 = 10 FOR UPDATE;`        prevents any other transaction from inserting, updating, or        deleting rows where the value of `t.c1` is        `10`.      



# 细节
首先明确,当通过索引查找数据时,innodb默认的方式是next-key lock.

但是如果不走索引,则是按页来锁数据的