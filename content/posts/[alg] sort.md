---
title: "[Algorithm] sort"
date: 2021-03-25
tags: ["Algorithm"]
categories: ["Algorithm"]
---

# 排序算法

## 稳定性

假定在待排序的记录序列中，存在多个具有相同的关键字的记录，若经过排序，这些记录的相对次序保持不变，即在原序列中，r[i]=r[j]，且r[i]在r[j]之前，而在排序后的序列中，r[i]仍在r[j]之前，则称这种排序算法是稳定的；否则称为不稳定的

[堆排序](https://baike.baidu.com/item/堆排序)、[快速排序](https://baike.baidu.com/item/快速排序)、[希尔排序](https://baike.baidu.com/item/希尔排序)、[直接选择排序](https://baike.baidu.com/item/直接选择排序)是不稳定的排序算法

[基数排序](https://baike.baidu.com/item/基数排序)、[冒泡排序](https://baike.baidu.com/item/冒泡排序)、[直接插入排序](https://baike.baidu.com/item/直接插入排序)、[折半插入排序](https://baike.baidu.com/item/折半插入排序)、[归并排序](https://baike.baidu.com/item/归并排序)是稳定的排序算法





## 快排

```go
package main

import (
	"fmt"
	"math/rand"
	"reflect"
	"sort"
)

func swap(a []int, i, j int) {
	a[i], a[j] = a[j], a[i]
}

func partition(a []int) int {
	r := rand.Int() % len(a)
	swap(a, r, len(a)-1)
	// j指针遍历数组a
	// i指针 a[:i]均是比a[len(a)-1]小的数
	i, j := 0, 0
	for j < len(a)-1 {
		if a[j] < a[len(a)-1] {
			swap(a, i, j)
			i++
		}
		j++
	}
	swap(a, i, len(a)-1)
	return i
}

func qsort(a []int) {
	if len(a) == 0 {
		return
	}
	mid := partition(a)
	qsort(a[:mid])
	qsort(a[mid+1:])
}

func main() {
	a := []int{rand.Int(), rand.Int(), rand.Int(), rand.Int(), rand.Int(), rand.Int(), rand.Int(), rand.Int()}
	b := make([]int, len(a))
	copy(b, a)
	sort.Ints(a)
	qsort(b)
	fmt.Println(reflect.DeepEqual(a, b))
}

```

## 归并

```go
// 此处其实可以充分利用a,b的有序性
func merge(a, b []int) {
	len := len(a) + len(b)
	a = a[:len]
	qsort(a) 
}

func msort(a []int) {
	if len(a) == 0 || len(a) == 1{
		return 
	}
	left := a[:len(a)/2]
	right := a[len(a)/2:]
	msort(left)
	msort(right)
	merge(left, right)
}

```

