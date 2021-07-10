---
title: "[Go] 设计模式-构造器 多步骤构建和柯里化"
date: 2021-07-10T12:23:27+08:00
tags : ["Go" ,"design-pattern"]
categories : ["Go"]
---

# 设计模式-构造器

想像这样一个场景,我们有一个工人类,工人可以吃饭,工作,睡觉

```go
type worker interface{
    eat()
    work()
    sleep()
}
```

但是如何获得一个工人呢?常见的我们有一个New函数用于构造:

```go
type workerImpl struct{
}

var _ worker = new(workerImpl)

func NewWorker() workerImpl {
    return &workerImpl{}
}
```

> 注意这里使用的常见的技巧有:
>
> 1. 返回实例,接收接口
> 2. 编译器断言某个结构体是否实现某接口

但是假如我们的workerImpl给构造是多步骤的呢? 比如,一个worker的构建需要

1. 注册
2. 签到
3. 培训
4. 验收

培训完后,我们对之前的步骤验收,一个worker就可以任意的调用eat,work,sleep了

## 方案1: worker

我们可以直接把前置条件耦合在worker的成员函数里,但显然,一个真正的worker只应该有eat/work/sleep这三个成员函数,其他的成员函数不应该属于worker

```go
w := workerImpl{}
w.Register()
w.CheckIn()
w.Study()
w.VerifyAll()

w.Work()
w.Eat()
w.Sleep()
```



## 方案2: builder

我们独立出一个builder构造类来专门做构造工作

```go
b := workerBuilder{}
b.Register()
b.CheckIn()
b.Study()
worker := b.Build()
```

这样,在每一步调用函数后得到的一些消息就可以保留在workerBuilder里面,链路传递下去

```go
type workerBuilder struct{
    registerInfo, checkInInfo , studyInfo string
}

func (wb workerBuilder) Build() *workerImpl{
    check(wb.registerInfo)
    check(wb.checkInInfo)
    check(wb.studyInfo)
    // 做一些其他事,这些事会依赖这三个字段
    return &workerImpl{}
}
```

缺点很明显,我们显式强制要求了register,checkin,study的调用顺序,但是对于程序员来说,这是无法控制的,使用者也许会先调用b.Study()

## 方案3: 柯里化,返回下一步的构造函数

> 什么是柯里化? 简单来说柯里化就是将一个函数多个参数变成多个函数一个参数,通过返回闭包函数的形式来引用之前的参数

```go
checkIn := RegisterWorker()
study := checkIn()
verify := study()
worker := verify()
```

如此一来,我们就很好的指定了下一步该调用哪个步骤

注意,每一步返回的函数都是一个闭包,这样就可以在全链路中传递`registerInfo, checkInInfo , studyInfo string`

比如:

```go
type checkIn func() study
type study func() verify
type verify func() workerImpl

func RegisterWorker() checkIn{
    registerInfo := register()
    return func() study{
        checkInInfo := checkIn(registerInfo)
        return func() verify{
            studyInfo := study(checkInInfo)
            return func () workerImpl{
                check(studyInfo)
                return workerImpl{}
            }
        }
    }
}
```

有时候,我们需要一些信息暴露出来,这也简单,函数返回即可

```go
registerInfo, checkIn := RegisterWorker()
fmt.Println(registerInfo)
var a int
fmt.Scanln(&a)
study := checkIn(a)
verify := study()
worker := verify()
```



这很好的使得用户调用代码简单了,但是随之带来一个问题,在多步骤构建过程中,代码会有较多缩进

不过只要我们将各个步骤的业务代码抽象成函数,只在柯里化中调用一个函数,然后返回下一个构建函数,还是可以接收的