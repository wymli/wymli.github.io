---
title: "[HTTP] Content-Type"
date: 2021-03-25
tags: ["HTTP"]
categories: ["HTTP"]
---

# About Content-Type
Content-Type 用来指定在POST请求中body的数据类型(或格式),是一个非常重要的Header字段
## 三种Content-Type
### application/x-www-form-urlencoded
- 默认类型,当form不指定enctype时使用此content-type
- 看名字就知道,urlencoded,当自己构造时,要对参数进行url转义
- 示例: `a=123&b=123`
- go语言中,可以直接传string/[]byte给body,也可以是map[string]string,也可以是url.Values(typedef map[string][]string)
  - 虽然这些都可以,但推荐url.Values,可以直接调用.encode(),自己构造的是没有encode的,但一般来说都没有问题,因为只有特殊字符需要encode!
- go server 解析:
  - 
### multipart/form-data(mime)
- 用于上传文件
- html form 构造: `form.enctype="multipart/form-data" i.put:type="file"`
- go client 构造: `import "mime/multipart"`
- go server 解析: 
  - 首先解析: `r.ParseMultipartForm(1024 * 1024)`
  - 取出来:`image := r.MultipartForm.Value["image"] `
- 也可以看看gin的api,更方便
### application/json
- json.marshall之后传进body即可


## gin解析:
```go
id := c.Query("id")
c.PostForm("name")
// 也可以bind进一个结构体
// 推荐使用bind,可以很方便的进行表单验证
// get:BindQuery , post:bindjson/bindxml/...
c.ShouldBind(&person)


// 单文件
router.MaxMultipartMemory = 8 << 20 
file, _ := c.FormFile("file")
c.SaveUploadedFile(file, dst)

// 多文件
form, _ := c.MultipartForm()
files := form.File["upload[]"]

```