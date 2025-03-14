---
title: "[c] trick1"
date: 2021-03-25
tags: ["C"]
categories: ["C"]
---

# 总结一下在c语言中遇到的诸多Tricks

## 柔性数组

一个典型的柔性数组如下所示,数组本身是不占空间的

```c
struct skipnode {
        int key;
        int value;
        struct sk_link link[0];
};

struct skipnode *node = malloc(sizeof(*node) + level * sizeof(struct sk_link));
```

关于柔性数组也可以看看redis的sds,也是用这个数组实现的

### 搭配Union

柔性数组也可以搭配Union联合体

```go
union node {
        node* next;
        char data[0];
};
```

这样,这个node既可以充当链表节点,指向下一个链表. 也可以使用data指向malloc后的分配的内存.



## 从成员还原出首地址

本质是我们需要知道偏移量,但我们不可能知道,这时可以借助编译器帮我们计算

完整代码是:

```c
#define list_entry(ptr, type, member) \
        ((type *)((char *)(ptr) - (size_t)(&((type *)0)->member)))
```

首先计算偏移量

```c
offset = (size_t)(&(((type *)0)->member)))
```

`((type *)0`表示将地址0解释为type类型,然后取出member,这自然的其内存地址就是相较于0的偏移,对其取值后转换成size_t,则就是字节偏移了

本质上等同于

```c
offset = (size_t)(&(((type *)123)->member))-123)
```





## void*泛型

...



