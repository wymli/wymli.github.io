---
title: "[Go] monkey patch"
date: 2021-03-25
tags: ["Go"]
categories: ["Go"]
---

# Monkey patch 猴子补丁

ref: https://bou.ke/blog/monkey-patching-in-go/

## Intro: 什么是monkey patch?

```go
package main

func a() int { return 1 }
func b() int { return 2 }

func main() {
	replace(a, b)
	print(a())  // 2
}
```

monkey patch将做到如上的效果,当你调用a函数时,实际却调用了b函数,看起来有点神奇!

这实际上是运行时改变了函数的行为

## 实现原理

We need to modify function `a` to jump to `b`’s code instead of executing its own body

```go
func replace(orig, replacement func() int) {
	bytes := assembleJump(replacement)  
	functionLocation := **(**uintptr)(unsafe.Pointer(&orig))
	window := rawMemoryAccess(functionLocation)
	
	copy(window, bytes)
}
```

- `bytes := assembleJump(replacement) `

  - 生成跳转replacement的机器码,将用它来替换跳转orig的机器码

  - ```go
    func assembleJump(f func() int) []byte {
    	funcVal := *(*uintptr)(unsafe.Pointer(&f))
    	return []byte{
    		0x48, 0xC7, 0xC2,
    		byte(funcVal >> 0),
    		byte(funcVal >> 8),
    		byte(funcVal >> 16),
    		byte(funcVal >> 24), // MOV rdx, funcVal
    		0xFF, 0x22,          // JMP [rdx]
    	}
    }
    ```

    

- `functionLocation := **(**uintptr)(unsafe.Pointer(&orig))`

  - 获取orig的函数位置

  - 注意,这里涉及函数赋值,原函数赋值给了orig,这也是原文为什么先分析func a(){} ; f := a的原因

  - 函数变量的内部结构(注意区分函数变量和函数):

    ```go
    type funcval struct {
        fn uintptr
        // variable-size, fn-specific data here (典型的,闭包的实现需要引用外部变量,放在这)
    }
    ```

    因此,functionLocation 将等于fn 

- `window := rawMemoryAccess(functionLocation)`

  - 获取由functionLocation开始的0xFF大小的内存空间

  - ```go
    func rawMemoryAccess(b uintptr) []byte {
    	return (*(*[0xFF]byte)(unsafe.Pointer(b)))[:]
    }
    ```

- `copy(window, bytes)`

  - 注意不是全部覆盖0xFF那么大,因为bytes没有那么大

