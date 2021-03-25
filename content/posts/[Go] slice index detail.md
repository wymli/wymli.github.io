---
title: "[Go] slice index detail"
date: 2021-03-25
tags: ["Go"]
categories: ["Go"]
---

# [Go] Slice的下标索引细节

在刷oj的时候,经常遇到要对一个数组取一部分的场景,用来递归分治

常见的比如快排,恢复二叉树等

在c/c++中,我会使用func(int* array , int lo , int hi)来标识数组的范围,但是在python这种动态语言中,可以直接使用数组的切片,很方便的传入递归函数 func (slice[lo:hi])

在go中,也有切片,也可以达到类似的效果,但是会存在一些你平时没有注意到的地方

## 1. a[len(a):]

对于边界情况,要注意: 

```go
a := []int{1,2,3}
len(a[:0]) == 0 // true
len(a[len(a):]) == 0 // true
len(a[cap(a):]) == 0 // true
```

对于Line#3/4,一定要注意,不会越界! 

> ```
> a[2:]  // same as a[2 : len(a)]
> a[:3]  // same as a[0 : 3]
> a[:]   // same as a[0 : len(a)]
> ```

只要按如上的规则还原low和high后,若满足 [rule](#rule) 就不会越界

但是如果cap=4,a[5:],就越界了

## 2. cap

一定要注意

- high是否越界取决于cap
- low是否越界取决于len

当我们往递归函数不断传入切片后,因为都在引用同一个底层内存,所以其实存在某些时候看似越界,实则是因为cap比len大的原因

如果想严格限制切片cap,那么在切片的时候,可以设置max参数:

```go
b := a[low : high : max]
```

## rule

这是spec上的切片下标的规则:

```go
0 <= low <= high <= max <= cap(a)
```

但我想补充一下:

```go
low和high都可以 >=len(a),只要小于cap(a),都是合法的
```

新切片:

`cap(b) = max - low , len(b) = high - low`

## ref

https://golang.org/ref/spec#Slice_expressions