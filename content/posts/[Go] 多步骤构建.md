---
title: "[Go] 多步骤构造器"
date: 2021-07-10T12:23:27+08:00
tags : ["Go" ,"design-pattern"]
categories : ["Go"]
---

# 设计模式-多步骤构造器

[TOC]

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
w.Verify()

w.Work()
w.Eat()
w.Sleep()
```

这显然很丑陋,并且不符合逻辑,我们

- 1: 无法控制用户对Register,CheckIn,Study,Verify的调用顺序
- 2: 也无法保证用户在Verify后不再调用这些前置条件函数

## 方案2: builder

为了解决问题2,我们独立出一个builder构造类来专门做构造工作

```go
b := workerBuilder{}
b.Register()
b.CheckIn()
b.Study()
worker := b.Build()
```

这样,build()后返回的workerImpl,可以只实现eat/sleep/work三个方法.

```go
type workerBuilder struct{
    registerInfo, checkInInfo , studyInfo string
}

func (wb workerBuilder) Build() *workerImpl{
    check(wb.registerInfo)
    check(wb.checkInInfo)
    check(wb.studyInfo)
    return &workerImpl{}
}
```

但是我们仍然没有解决register,checkin,study的调用顺序问题,用户也许先调用Study再Register

## 方案3: 柯里化,返回下一步的构造函数

> 什么是柯里化? 简单来说柯里化就是将一个函数多个参数变成多个函数一个参数,通过返回闭包函数的形式来引用之前的参数

```go
checkIn := RegisterWorker()
study := checkIn("1")
verify := study("B")
worker := verify("1")
```

如此一来,我们就很好的指定了下一步该调用哪个步骤

> 注意,每一步返回的函数都是一个闭包,这样就可以在全链路中传递`registerInfo, checkInInfo , studyInfo string`

比如:

```go
type checkIn func(checkInCode string) study
type study func(studyClass string) verify
type verify func(verifyCode string) workerImpl

func RegisterWorker() checkIn {
    registerInfo := registerF()
    return func(checkInCode string) study{
        checkInInfo := checkInF(registerInfo,checkInCode)
        return func(studyClass string) verify{
            studyInfo := studyF(checkInInfo, studyClass)
            return func(verifyCode string) workerImpl{
                if ok := verifyF(studyInfo , verifyCode);ok{
                    return workerImpl{...}
                }
                return nil
            }
        }
    }
}
```

有时候,我们需要一些信息暴露出来,这也简单,函数返回即可

```go
func RegisterWorker() (string, checkIn) {
    registerInfo := registerF()
    return registerInfo , func(checkInCode string) study{
        // ...
    }
}
```



这很好的使得用户调用代码简单了,但是随之带来一个问题,在多步骤构建过程中,代码会有较多缩进

不过只要我们将各个步骤的业务代码抽象成函数(指上例中的`register()`,`checkIn(registerInfo)`,`study(checkInInfo)`等函数),只在柯里化中调用一个函数,然后返回下一个构建函数,还是可以接收的

## 方案4: 装饰函数以避免callback hell

用函数wrap<装饰器decorate>代替闭包匿名函数

```go
type checkIn func(checkInCode string) study
type study func(studyClass string) verify
type verify func(verifyCode string) workerImpl

func RegisterWorker() checkIn {
    registerInfo := registerF()
    return checkInWrap(registerInfo)
}

func checkInWrap(ri *registerInfo) checkIn{
    return func(checkInCode string) study{
        checkInInfo := checkInF(ri,checkInCode)
        return studyWrap(checkInfo)
    }
}

func studyWrap(ci *checkInInfo) study{
    return func(studyClass string) verify{
        studyInfo := studyF(ci, studyClass)
        return verifyWrap(studyInfo)
    }
}

func verifyWrap(si *studyInfo)verify{
    return func(verifyCode string) workerImpl{
        if ok := verifyF(si , verifyCode);ok{
            return workerImpl{...}
        }
        return nil
    }
}
```

原理:我们之前使用闭包的原因就是为了获取`registerInfo,checkInInfo,studyInfo`这些数据,所以也可以使用wrap把他们包起来,作为函数参数传入,效果是一样的

其实闭包就相当于匿名函数,这里的wrap就是具名函数,匿名函数天然获取外部数据引用,具名函数通过显式传参来获取引用.