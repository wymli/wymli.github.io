---
title: "[arch] design pattern"
date: 2021-03-25
tags: ["arch"]
categories: ["arch"]
---

# 设计模式

聊聊我熟悉的设计模式

首先,推荐一下这门课: https://time.geekbang.org/column/intro/100039001

我看了目录,确实很有吸引力,可惜太贵了:(

## 创建型

用于创建类型

### 单例

单例模式常用于创建全局唯一变量,大多数时候都增加了耦合,降低了可测试性

直接使用`sync.Once`,只调用一次是由once变量保证的

```go
type Once struct {
	done uint32
	m    Mutex
}
```

使用示例:

```go
package singleton

var (
    once sync.Once
    GlobalStatus map[string]string
)

func New() singleton {
	once.Do(func() {
		GlobalStatus = make(map[string]string)
	})
	return GlobalStatus
}
```

实现:

```go
func (o *Once) Do(f func()) {
	// Note: Here is an incorrect implementation of Do:
	//	if atomic.CompareAndSwapUint32(&o.done, 0, 1) {
	//		f()
	//	}
	if atomic.LoadUint32(&o.done) == 0 {
		o.doSlow(f)
	}
}

func (o *Once) doSlow(f func()) {
	o.m.Lock()
	defer o.m.Unlock()
	if o.done == 0 {
		defer atomic.StoreUint32(&o.done, 1)
		f()
	}
}
```

> 注释说的很清楚,一个简单的CAS是不行的!
>
> 我们必须在f()调用完后,再将o.done置位

> 

### 工厂

以根据不同的文件名后缀创建不同的解析器为例

#### 简单工厂

直接根据不同的后缀,返回不同的解析器实例

#### 工厂方法

直接根据不同的后缀,返回不同的解析器工厂,由该工厂去创建解析器实例

实现上,一般用map存各个解析器工厂

> 好处: 如果要添加新的解析器,只需要在map中添加即可,而不需要改变逻辑代码

#### 抽象工厂

直接根据不同的后缀,返回不同的解析器工厂,该解析器工厂可以创建不同类的解析器

> 即不仅是不同类产品,同类产品本身也有区别
>
> 比如解析器,分为json parser,xml parser... 对于json parser本身,还分为fast json parser, portable json parser..等

