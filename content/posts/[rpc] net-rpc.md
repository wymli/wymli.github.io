---
title: "[rpc] net/rpc"
date: 2021-03-27
tags: ["rpc"]
categories: ["rpc"]
---

# net/rpc

如下是一段极简的net/rpc代码, `client.Call()`代表这是一个同步的rpc,如果是异步,net/rpc提供了`client.Go()`方法,典型的实现是返回一个chan,当异步完成时,这个chan就会读出消息(当然,net/rpc的Go()不是完全这样实现的,但也差不多)

## 示例代码

```go
package main

import (
	"fmt"
	"net"
	"net/rpc"
	"time"
)

type ServiceA struct{}

func (a *ServiceA) A(req int, reply *int) error {
	fmt.Println("server recv:", req)
	*reply = 2
	return nil
}

func server() {
	ls, err := net.Listen("tcp", ":9090")
	if err != nil {
		panic(err)
	}
	rpc.Register(new(ServiceA))
	for {
		rpc.Accept(ls)
	}
}

func main() {
	go server()
	time.Sleep(1 * time.Second)

	client, err := rpc.Dial("tcp", ":9090")
	if err != nil {
		panic(err)
	}
	var ax int
	err = client.Call("ServiceA.A", 1, &ax)
	if err != nil {
		panic(err)
	}
	fmt.Println("client: recv:", ax)
}

```

## 服务注册

通过`rpc.Register()`注册某个对象,该对象的所有导出方法都会被识别

事实上,一个过程需要满足下面的条件才能被成功注册:

1. 对象是导出的
2. 对象的方法是导出
3. 该方法只接受两个参数并返回error,一个是请求参数,一个是返回值,其中第二个reply应该是指针的形式.

```go
rpc.Register(new(ServiceA))
// 或
rpc.Register(&ServiceA{})
```

## 服务调用

通过类名+方法名来调用函数

```go
err = client.Call("ServiceA.A", 1, &ax)
```

## 编解码

`net/rpc`使用了`gob`作为编解码器

在使用时屏蔽了所有底层的输入输出,简单的encode,decode即可还原出想要的结构体,完全不需要在意分包之类的细节

```go
type gobClientCodec struct {
	rwc    io.ReadWriteCloser
	dec    *gob.Decoder
	enc    *gob.Encoder
	encBuf *bufio.Writer
}

codec := &gobClientCodec{conn, gob.NewDecoder(conn), gob.NewEncoder(encBuf), encBuf}


func (c *gobClientCodec) WriteRequest(r *Request, body interface{}) (err error) {
	if err = c.enc.Encode(r); err != nil {
		return
	}
	if err = c.enc.Encode(body); err != nil {
		return
	}
	return c.encBuf.Flush()
}

func (c *gobClientCodec) ReadResponseHeader(r *Response) error {
	return c.dec.Decode(r)
}

func (c *gobClientCodec) ReadResponseBody(body interface{}) error {
	return c.dec.Decode(body)
}
```



## 通信机制

net/rpc并没有采用典型的一个req一个resp的形式,而是在创建client时,就开启一个goroutine去监听recvbuff,对读到数据包,解析出其中的一个seq字段,用来和当初的req对应,因此,当发送rpc请求的时候,字段会包含seq

本机使用一个map来存储映射关系,Call 结构体就代表一个调用过程,实际上调用Go()方法的异步调用就会返回/*Call,我们需要判断call.Done来识别调用的完成

```go
pending  map[uint64]*Call

type Call struct {
	ServiceMethod string      // The name of the service and method to call.
	Args          interface{} // The argument to the function (*struct).
	Reply         interface{} // The reply from the function (*struct).
	Error         error       // After completion, the error status.
	Done          chan *Call  // Receives *Call when Go is complete.
}
```

## 数据结构

```go
type Request struct {
	ServiceMethod string   // format: "Service.Method"
	Seq           uint64   // sequence number chosen by client
	next          *Request // for free list in Server
}
type Response struct {
	ServiceMethod string    // echoes that of the Request
	Seq           uint64    // echoes that of the request
	Error         string    // error, if any.
	next          *Response // for free list in Server
}
```

### 发送

```go
err := client.codec.WriteRequest(&client.request, call.Args)
```

### 接收

```go
response = Response{}
err = client.codec.ReadResponseHeader(&response)
call := client.pending[response.Seq]
err = client.codec.ReadResponseBody(call.Reply)
call.Done <- call
```

```go
func (client *Client) Call(serviceMethod string, args interface{}, reply interface{}) error {
	call := <-client.Go(serviceMethod, args, reply, make(chan *Call, 1)).Done
	return call.Error
}
```

