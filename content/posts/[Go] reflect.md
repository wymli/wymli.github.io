---
title: "[Go] reflect"
date: 2021-03-25
tags: ["Golang"]
categories: ["Golang"]
---

## 什么是反射?

反射提供了一种运行时能对对象增删查改的方法.

换句话说,当函数参数的interface{}时,提供了一种访问原来的类型和值的方法. 这与switch type类似,但是switch只能对type进行判断,而你根本不知道会传进来何种自定义的结构体,这就是需要判断reflect.kind了

## (Value) Elem() Value

>  Elem returns the value that the interface v contains or that the pointer v points to. It panics if v's Kind is not Interface or Ptr. It returns the zero Value if v is nil.

reflect.Value.Elem(),必须接收Interface或Ptr类型的Kind,它将会返回其指向或包含的类型.

这很好理解,如果reflect.Value{&a},那么Elem()后,就会返回reflect.Value{a}.

但是,什么时候reflect.Value会是一个Interface呢?

### ValueOf(i interface{}) Value

>  ValueOf returns a new Value initialized to the concrete value stored in the interface i. ValueOf(nil) returns the zero Value.

当我们执行如下代码时:

```go
var i interface{} = 1
x := reflect.ValueOf(i).Kind()
fmt.Println(x) // int
```

为什么呢? 

- 明明传入的是一个interface{}类型的 i

再看文档,它明确的说明了 initialized to the concrete value stored in the interface,因此,具体值将会被取出,那么既然都会被取出,难道还存在interface包一个interface吗? 即取出来后还是一个interface?

- 答案是不可能的,https://blog.golang.org/laws-of-reflection 说明了 An interface variable can store any concrete (non-interface) value

再看另一个问题,为什么reflect.ValueOf一定要把interface里面的具体值取出来呢,留在那里,我们自己调用Elem取出来不行吗?

- 我们要注意,reflect.ValueOf(i interface{})的函数签名,我们知道对于空接口,其内部和reflect.Value是类似的结构,都是(type,dataPtr)

- 如果传入的是a (int, &1),那么首先发生简单的浅复制: i = a => i(int,&1). 然后返回reflect.Value{i.type,i.dataPtr,...},可以看出,所谓的取出,本质是interface{}的type,dataPtr被复制转移到了reflect.Value

- 如果传入的是&a, 那么经过浅复制,i将会是 (interface , &a). 这是自然的,对x T取地址&x将产生*T指向x,所以&a将产生\*interface{}指向a

```go
func test(i interface{}) {
	switch i.(type) {
	case *int:
		fmt.Println("*int")
	case int:
		fmt.Println("int")
	case *interface{}:
		fmt.Println("*interface")
	default:
		fmt.Println("not this")
	}
}
func main(){
    var i interface{} = 1
	test(i)  // int
	test(&i)  // *interface
}
```



## Value.Kind() == Interface

执行如下代码:

```go
var i interface{} = 1
x := reflect.ValueOf(i).Kind()
fmt.Println(x)  // int
fmt.Println(reflect.ValueOf(&i).Elem().Kind()) // interface
v := reflect.ValueOf(struct{ a interface{} }{1})
fmt.Println(v.Field(0).Kind()) // interface
```

当我们传递&i给ValueOf的时候,就会返回一个Ptr,然后我们调用Elem(),便得到了interface

或者访问结构体的字段,也可以得到interface.

## Type.Kind() == Interface

前面介绍了Value.Kind(),与之类似的,还有Type.Kind()

reflect.TypeOf([]interface{}{1, 2}).Elem().Kind() == reflect.Interface // true

>  (Type)Elem() : Elem returns a type's element type. It panics if the type's Kind is not Array, Chan, Map, Ptr, or Slice.

