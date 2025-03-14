---
title: "[Go] escape analysis"
date: 2021-03-25
tags: ["Golang"]
categories: ["Golang"]
---

# 逃逸分析

首先,逃逸分析发生在编译时,由分析结果决定运行时对象应该在堆还是栈上分配

注意: 这个编译时分析似乎是以函数为单位的静态分析,因此才有当函数参数是interface{}时,不知其具体类型

## 规则

- 堆对象不能指向栈对象,否则栈对象被分配在堆上
- 其他....

## 典型场景

### 1.函数返回指向栈内对象的指针

```go
func NewA()*a{
    return &a{123}
}
```

### 2.调用反射(interface{}动态类型)

在反射的实现中,比如 reflect.ValueOf :

```go
func ValueOf(i interface{}) Value {
	if i == nil {
		return Value{}
	}
    // TODO: Maybe allow contents of a Value to live on the stack.
	// For now we make the contents always escape to the heap. It
	// makes life easier in a few places (see chanrecv/mapassign
	// comment below).
	escapes(i)
	return unpackEface(i)
}
```

直接对i逃逸了,那么i指向的内存必然也逃逸,所以传进去的值便逃逸了

> 因此,不是说往func(interface{})传值,或者往func(*struct)传指针就会导致逃逸分析.

> 只是大多数场景下,其内部都会用到反射,导致逃逸(switch type不会导致逃逸)

### 拼接字符串

比如:

```go
var strt = "asdf"
//go:noinline
func t(i *int) string{
	*i += 1
	return "asdf"+strt
}
```

```go
.\a.go:15:15: "asdf" + strt escapes to heap
```

很奇怪,直接return string("asdf")却不会导致逃逸,按道理string{ptr,len}的结构,这个ptr应该会逃逸才对

## -gcflags "-m -l"

- -m 设置打印信息
- -l禁止内联, 也可用`//go:noinline`

三个典型输出的意义: (https://groups.google.com/g/golang-dev/c/Cf4tpaWP6rc)

> "moved to heap" means that a local variable was allocated on the heap
>
> rather than the stack.

> "leaking param" means that the memory associated with some parameter
>
> (e.g., if the parameter is a pointer, the memory to which it points)
>
> will escape.  This typically means that the caller must allocate that
>
> memory on the heap.

> "escapes to heap" means that some value was copied into the heap.
>
> This differs from "moved to heap" in that with "moved to heap" the
>
> variable was allocated in the heap.  With "escapes to heap" the value
>
> of some variable was copied, for example when assigning to a variable
>
> of interface type, and that copy forced the value to be copied into a
>
> newly allocated heap slot.

 "moved to heap" and "escapes to heap" both always mean a heap  allocation occurs. The difference is "moved to heap" is used for named  variables, and "escapes to heap" is used for anonymous variables (e.g.,  as allocated by "new" or "make"; taking the address of a composite  literal).

个人理解:

move常用于普通变量的,由于生命周期的原因导致的需要分配在堆上

escape常用于匿名变量,比如st.a = new(int),或者传入interface{}

#### 编译指令

运行时判断一个对象在不在堆上

> 一般的,如果//后没有空格,那么就是编译指令,常见的还有generate

> https://www.yuque.com/flipped-aurora/gqbcfk/io1db4

```go
//go:linkname inheap runtime.inheap
func inheap(b uintptr) bool

// example
println(inheap(uintptr(unsafe.Pointer(&m))))
println(inheap(uintptr(unsafe.Pointer(m.b))))
```

## 其他

个人感觉,不必深究,知道基础的就好

声明:看看就好,不一定对