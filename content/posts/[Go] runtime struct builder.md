---
title: "[Go] runtime struct builder"
date: 2021-03-25
tags: ["Golang"]
categories: ["Golang"]
---

# Runtime Struct: 运行时结构体构造方法

参考:

https://github.com/itsubaki/gostruct

https://pkg.go.dev/reflect#example-StructOf

## reflect.New(typ reflect.Type) reflect.Value

> New returns a Value representing a pointer to a new zero value for the specified type. That is, the returned Value's Type is PtrTo(typ).

因此,给定一个结构体类型的type,我们就可以构造出value

## reflect.StructOf(fields []reflect.StructField) reflect.Type

> StructOf returns the struct type containing fields. The Offset and Index fields are ignored and computed as they would be by the compiler.
>
> StructOf currently does not generate wrapper methods for embedded fields and panics if passed unexported StructFields. These limitations may be lifted in a future version.

因此,给定[]reflect.StructField,就可以构造出type

注: 其他类型同理,比如reflect.ChanOf,reflect.ArrayOf,reflect.SliceOf

## reflect.StructField

```go

// A StructField describes a single field in a struct.
type StructField struct {
	// Name is the field name.
	Name string
	// PkgPath is the package path that qualifies a lower case (unexported)
	// field name. It is empty for upper case (exported) field names.
	// See https://golang.org/ref/spec#Uniqueness_of_identifiers
	PkgPath string

	Type      Type      // field type
	Tag       StructTag // field tag string
	Offset    uintptr   // offset within struct, in bytes
	Index     []int     // index sequence for Type.FieldByIndex
	Anonymous bool      // is an embedded field
}
```

根据reflect.StructOf的文档和自身的注释(见上文),Offset,Index都不需要指定,Anonymous也不支持(go1.13),name必须capital,PkgPath也为空

总结来说,我们需要指定:

```go
iField := reflect.StructField{
    Name: "Id",
    Type: reflect.TypeOf(uint64(0)),
    Tag:  `json:"id"`, // optional
}
```

## Build

```go
typ := reflect.StructOf([]reflect.StructField{
    {
        Name: "Height",
        Type: reflect.TypeOf(float64(0)),
        Tag:  `json:"height"`,
    },
    {
        Name: "Age",
        Type: reflect.TypeOf(int(0)),
        Tag:  `json:"age"`,
    },
})

v := reflect.New(typ).Elem()
v.Field(0).SetFloat(0.4)
v.Field(1).SetInt(2)
s := v.Addr().Interface()
```

一般来说,使用时,比如将其返回,要转换成Interface{}

为了方便的用string访问字段,而不是index,我们可以自己包装一层,然后加上Interface(),Addr()两个方法

```go
type myStruct struct {
	internal reflect.Value
	index    map[string]int
}

func (i *myStruct) Field(name string) reflect.Value {
	return i.internal.Field(i.index[name])
}

func (i *myStruct) Interface() interface{} {
	return i.internal.Interface()
}

func (i *myStruct) Addr() interface{} {
	return i.internal.Addr().Interface()
}
```

调用Addr()方法,可用于取地址,常用于调用指针接收者的方法

> Addr is typically used to obtain a pointer to a struct field or slice element in order to call a method that requires a pointer receiver.

## 用处

母鸡,暂时不太知道运行时构建结构体的用处

我唯一用到反射的地方,就只有解析结构体字段了,比如把struct转成map这种

但是以此来作为熟悉refelct包,还是不错的

