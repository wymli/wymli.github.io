---
title: "[Go] 单测"
date: 2021-06-25T12:23:27+08:00
tags : ["Go" ,"ut"]
categories : ["Go"]
---

# 单测

单测在业务开发的重要性中不言而喻,在常见的epc规范中,一般的存量覆盖率要求达到50%,增量覆盖率要求达到80%.

> 当然,这个很教条,我们一般只测有意义的目录,对于像config目录,dao目录测试的必要性不是很高

常用的单测脚本:

```sh
go test ./... -coverprofile=cover.out -covermode=conut -gcflags=all=-l -v

排除掉某些路径:
go test $(go list ./... | grep -v "/neverTest") -coverprofile=cover.out -covermode=conut -gcflags=all=-l -v
```

[TOC]



## 打桩

最完美的开发方式当然是依赖注入,但是很多时候我们并没有这么完美的设计,或者简单的业务其实也不值得去多么精心设计,所以不可避免的在单测中要用上打桩框架,运行时替换目标函数/变量的值

> 其实现原理就是改变目标被替换函数的跳转地址,使其跳转到替换函数上来

>  Monkey implements monkeypatching by rewriting the running executable at runtime and inserting a jump to the function you want called instead. **This is as unsafe as it sounds and I don't recommend anyone do it outside of a testing environment.**

> __只能在单测中使用__

### 三大框架

目前业界在用的,基本就是三大框架

#### monkey

- 优点: 使用简单
- 缺点: 不支持序列结果

```
go get -u -v bou.ke/monkey
```

```go
打桩普通函数
monkey.Patch(<target function>, <replacement function>)

monkey.Patch(fmt.Println, func(a ...interface{}) (n int, err error) {
    s := make([]interface{}, len(a))
    for i, v := range a {
        s[i] = strings.Replace(fmt.Sprint(v), "hell", "*bleep*", -1)
    }
    return fmt.Fprintln(os.Stdout, s...)
})
```

```go
打桩成员函数
monkey.PatchInstanceMethod(<type>, <name>, <replacement>)

monkey.PatchInstanceMethod(reflect.TypeOf(d), "Dial", func(_ *net.Dialer, _, _ string) (net.Conn, error) {
    return nil, fmt.Errorf("no dialing allowed")
})
```

```go
在原函数调用和新函数调用之间切换
monkey.PatchGuard

guard = monkey.PatchInstanceMethod(reflect.TypeOf(http.DefaultClient), "Get", func(c *http.Client, url string) (*http.Response, error) {
    guard.Unpatch()
    defer guard.Restore()

    if !strings.HasPrefix(url, "https://") {
    return nil, fmt.Errorf("only https requests allowed")
    }

    return c.Get(url)
})
```

> 因为我们只在单测中使用patch,所以parchGuard的使用场景较少

#### gomonkey

```
go get github.com/agiledragon/gomonkey
```

使用上差别不大

```
func ApplyFunc(target, double interface{}) *Patches
func ApplyFuncSeq(target interface{}, outputs []OutputCell) *Patches

func ApplyFuncVar(target, double interface{}) *Patches
func ApplyFuncVarSeq(target interface{}, outputs []OutputCell) *Patches

func ApplyGlobalVar(target, double interface{}) *Patches

func ApplyMethod(target reflect.Type, methodName string, double interface{}) *Patches
func ApplyMethodSeq(target reflect.Type, methodName string, outputs []OutputCell) *Patches
```

使用示例:

```go
// func rpc(name string) (string, error)

outputs := []gomonkey.OutputCell{
    {Values: gomonkey.Params{"1", nil}}, 
    {Values: gomonkey.Params{"2", nil}}, 
    {Values: gomonkey.Params{"3", nil}},
}
gomonkey.ApplyFuncSeq(rpc, outputs)
```



#### gomock

> 需要搭配mockgen使用,针对接口的定义直接生成一个mock实现

此处略,不够轻量.

虽然一般根据proto文件生成桩代码时也会一起用mockgen生成mock代码,但其实一般还是不太用这个.

用gomonkey足以适用大部分场景

### 面对接口

我们没办法mock接口,也就是说,如果a是接口变量,那么它的成员函数我们是没办法mock的,我们只能mock b的成员函数,b是a的具体实现,比如:

```go
type a interface{
    Say func()
}
func NewA() a{
    return &default{}
}
func Test_x(...){
    // x := NewA()
    // gomonkey.ApplyMethod(reflect.Typeof(x),"Say",...) // useless
    b := ...
    gomonkey.ApplyFunc(NewA , func()a{return &b})
    gomonkey.ApplyMethod(reflect.Typeof(b),"Say",...)  // ok
}
```

> 当然一般这种返回接口的,都会提供NewMockA这个函数供我们调用

> 这也涉及一个设计原则: 返回实例,接收接口; 
>
> 即函数返回值应该是某个实例,函数的参数应该是某个接口



## 断言

一般的,我们适用表驱动的单测,所以assert就不是那么重要了,一般我们只判断一下函数结果是不是相等即可

#### goconvey

https://github.com/smartystreets/goconvey

非常适合做行为测试,但是我们一般好像都只是做一下结果测试

testtify

```
"github.com/stretchr/testify/assert"
```

```
func TestSomething(t *testing.T) {
  // assert equality
  assert.Equal(t, 123, 123, "they should be equal")
}
```