---
title: "[Go] short var declare"
date: 2021-03-25
tags: ["Go"]
categories: ["Go"]
---

# [Go] 短变量声明 := 

在Go中,提供了动态语言常用的一种直接声明并赋值的语法糖,即 := 短变量声明

> := 这个符号,可能是借鉴了Pascal

短变量声明有一定的要注意的地方,它与先声明后赋值有着一定的区别:



1 短变量声明无法用于全局变量的创建



2 短变量定义函数时无法使用递归

```go
a := func(){
    a() // undeclared name: a
}

var a func()
a = func(){
    a()  // ok!
}
```



3 多变量赋值,左端必须有一项是新定义的变量

- 若在同一作用域, 已存在的变量将被覆盖. 否则,是定义新的局部变量

```go
a,_ := f()
if a,err := f();!err{
    a++
}
fmt.Println(a) // 这个a还是原来的a,因为if{}是个局部作用域
```

