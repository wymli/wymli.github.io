---
title: "[Go] release notes"
date: 2025-05-10
categories : ["golang"]
tags : ["golang"]
---

> 原文: https://c6t4wbgxht.feishu.cn/docx/Nu9sd0FobokaxMxEddxc9VTXnIg

https://tip.golang.org/doc/devel/release
# 1.18
1. 加入泛型
2. 新增包：golang.org/x/exp/constraints
3. 新增包：golang.org/x/exp/slices
4. 新增包：golang.org/x/exp/maps
5. 新增 fuzz test
6. go get 不再拥有go install的能力
7. go编译时注入额外的版本控制信息到binary中，可以在代码里获取，也可以直接从二进制获取
  1. 现在可以直接通过go version -m ${bin} 看到对应的vcs（比如git）的一些信息，比如代码对应的最后一次commit的时间，编译用的go版本等
  2. 也可以import debug/buildinfo 在代码中获取这些信息
  3. 需要注意的是，build time这个东西还是只能通过-ldflags="-X 'main.buildTime=$(date)'" 在编译时注入
8. 支持Workspace mode，如果在当前目录或父目录有go.work file，或者通过GOWORK env指定了go.work文件地址, 用来支持多个main module（比如原来vscode只支持单个go.mod file）
# 1.19
1. 内存模型：The Go memory model has been revised to align Go with the memory model used by C, C++, Java, JavaScript, Rust, and Swift. 
  1. 引入 debug.SetMemoryLimit , 设置后，当堆+非堆内存到达对应设置的soft memory后，强制gc一次
2. atomic包增加原子类型，比如atomic.Bool, 在之前atomic只有原子操作，没提供类型
# 1.20
1. 没啥特别的
# 1.21
1. 引入 min and max 
2. 引入 clear, 可以 clear map/slice, 需要注意的是，对map，是清空，len变0；对slice，是将元素清零，但是len不变
3. 新增 log/slog， 结构化日志
4. slices/maps包增加通用泛型方法
5. sync增加 sync.OnceFunc, OnceValue...，不再只是sync.Once
# 1.22
1. for训练的value每次迭代时都会创建新的
2. 支持 for range ${n}
3. 支持  range-over-function iterators 函数迭代器
# 1.23
1. 增加iter包, 了解下iter.Seq, 迭代器类型，迭代器可以被for range使用，也可以直接传入yield函数（其实感觉更像是handle函数）
  1. iter.Seq 就是一个函数的别名
type (
        Seq[V any]     func(yield func(V) bool)
        Seq2[K, V any] func(yield func(K, V) bool)
)
# 1.24
1. 增加很多基于iter的util方法