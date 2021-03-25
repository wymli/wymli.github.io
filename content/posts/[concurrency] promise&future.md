---
title: "[concurrency] promise&future"
date: 2021-03-25
tags: ["concurrency"]
categories: ["concurrency"]
---

# Promise&future

函数式编程是一个新的编程范式,基本上,只要你的编程语言支持`函数是一等公民`这个说法,那么就至少支持部分的函数式编程



[TOC]



## promise

所谓的promise,是指对异步函数返回值的一个封装,比如就是对单个int的封装,但是由于是异步的,所以只能注册回调函数来完成当函数结束后对int进行访问

我们知道对异步函数的一般做法是,创建的同时要传入回调函数,比如:

```go
func createAudioFileAsync(successCallback func(result interface{})interface{}, failureCallback func(err interface{})interface{}) interface{}{
    go func(){
       	// dosomething
        if ok{
            return successCallback(result)
        }else{
            return failureCallback(err)
        }
    }()
}
```

这里`successCallback func(result interface{}), failureCallback func(err interface{})`这些函数可以传入闭包,如果希望同时修改外部变量,这就是某种意义上的观察者模式

```go
createAudioFileAsync(func(resutlt interface{}){
    //dosomething
},func(err interface{}){
    //dosomething
})
```

但很明显,这陷入了某种意义上的回调地狱(callback hell),比如如果我们想有多步,先执行func1,成功了就执行func2,再成功就执行func3,...

```go
func func1/2/3 (succCb , failCb){
    // dosomthing
    if ok{
        succCb()
    }else{
        failCb()
    }
}

func1(
    func2(
        func3(
            func(resutlt interface{}){
    			//dosomething
			},func(err interface{}){
    			//dosomething
			}
        ),func(err interface{}){
    		//dosomething
        }
    ),func(err interface{}){
    }
)

//如果写的清晰一点,就是:
func1(
    func2(
        func3(
            func(resutlt interface{}){
    			// dosomething
			},failureCallback
        ),failureCallback
    ),failureCallback
)
```

于是,Promise引入了,我们不再直接在异步函数参数中传递callback,而是让异步函数返回一个promise,这个promise结构体支持注册回调,哪怕异步函数已经完成了,也会触发一次回调;

这样,__原本嵌套的回调函数,变成了级联的调用链__

```go
func func1()promise{
    // dosomthing
    return promise
}

promise := func1()
promise.then(func(resutlt interface{}){
    // dosomething
},failureCallback)
```

级联调用时(`successCb()`要返回promise):

```go
func1().then(func(){return func2()},failureCallback).then(func(){return func3()},failureCallback)
```

为了更好的减少代码,我们将`failureCallback`抽离,形成一个统一的错误处理

```go
func1().then(func(){return func2()}).then(func(){return func3()}).catch(failureCallback)
```

> 一般的,每个`successCb`都应该以一个result为参数,在go里面,可以用interface{}替代,假装自己是动态类型

## await

 `async/await` 是promise的语法糖,可以不必再刻意的写出`.then()`调用链

比如如下代码,只要有一个await失败,就直接跳转到catch

```go
async function foo() {
  try {
    const result = await doSomething();
    const newResult = await doSomethingElse(result);
    const finalResult = await doThirdThing(newResult);
    console.log(`Got the final result: ${finalResult}`);
  } catch(error) {
    failureCallback(error);
  }
}
```



> async函数,代表这是一个可能的异步函数(如果async内部不包含await,那么就失去async语义,转为同步函数)
>
> async函数可能包含0个或者多个[`await`](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Operators/await)表达式。await表达式会暂停整个async函数的执行进程并出让其控制权，只有当其等待的基于promise的异步操作被兑现或被拒绝之后才会恢复进程。promise的解决值会被当作该await表达式的返回值。使用`async` / `await`关键字就可以在异步代码中使用普通的`try` / `catch`代码块。

## C++中的future/promise

```cpp
std::promise<int> p;
std::future<int> f3 = p.get_future();
std::thread( [&p]{ p.set_value_at_thread_exit(9); }).detach();
f3.wait();
```

> 这里detach,是指分离这个thread,让他独立执行,而不再需要主线程join()来回收资源,可以回顾进程中的僵尸进程,就是子进程执行完了,但是父进程没有join它(wait/waitpid),导致资源未回收

可以看出,这里future,就是异步值的承载,是只读的,promise则用来设置值,是只写的

如果以go语言为例,__promise就是管道的左端,chan <- ,future就是管道的右端<- chan__

> 注意,使用promise/future时,就不再只限定于返回值了,可以异步执行的过程中,由promise.setValue,和go的channel很像



当然,也可以直接将返回值作为future

```go
std::future<int> f2 = std::async(std::launch::async, [](){ return 8; });
f2.wait()
f2.get()
```



## Go中的future/promise

如上所述

```go
asyncTask := func(){
    ch := make(chan int,1)
    go func(){
        //dosomething
        ch<-1 // work as a kind of promise
    }()
    return ch
}
future := asyncTask()
<- future // this will be blocked
```

当然,对future的读会导致阻塞,我们可以再包装一下

```go

asyncTask := func(){
    promise := &promise_st{}
    go func(){
        //dosomething
        promise.SetVal(1)
    }()
    return promise.getFuture()
}
future := asyncTask()

future.Wait()
val := future.get()
```

设计上也不难,本质是个单生产者,单消费者的问题

```go

type promise_st struct{
    val interface{}
    ok bool
    ch chan interface{}
}
func (p *promise_st) SetVal(a interface{}){
    ch <- a
}
func (p *promise_st) Wait(){
    p.val = <- ch
    //atomic.CAS(&p.ok , false , true)
    p.ok = true
}
func (p *promise_st) Get()interface{}{
    if p.ok{
        return p.val
    }
    return nil
}
```

由于go的channel已经足够强大,所以到没必要去使用future/promise,await/async

但是知道这些东西还是很有必要的