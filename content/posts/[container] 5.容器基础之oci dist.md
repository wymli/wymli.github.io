---
title: "[container] 5.容器基础之oci dist"
date: 2025-03-09
categories : ["container"]
tags : ["container", "oci"]
---

oci distribution spec 比较简单，就是定义了一些用于pull/push 的api

> 一个有趣的事实是，oci registry 不只是存储镜像，也可以用于存储helm chart。

# Pull
## Pull manifest
1. GET /v2/<name>/manifests/<reference> 
    1. name: 一般是${namespace/image_name}, 比如 library/nginx
    2. reference：一般是digest或者tag，比如latest、v1.2.3、sha256:abc123...
2. 拉取下来的是符合oci image spec的manifest文件

## Pull blobs
1. GET /v2/<name>/blobs/<digest>

# Push
值得注意的是，在push image时，是先push blobs，再push manifest，与pull相反
## Push blobs
1. 单次Post
    1. 直接往 /v2/<name>/blobs/uploads/?digest=<digest> 进行Post，body就是blob二进制内容
2. 先Post再Put
    1. Post /v2/<name>/blobs/uploads/ 拿到 upload url(upload url将被放在rsp header里的Location字段)
        1. 这里的location url往往是专用存储的地址，比如s3
    2. 随后上传二进制到 <Location>?digest=<digest>
3. 分块上传
    1. 不再赘述，和http chunk机制有关
4. digest:
    1. 值得注意的是:
        1. A config file references the uncompressed layer contents by sha256.
        2. A manifest references the compressed layer contents by sha256 and the size of the layer.
        3. A manifest references the config file contents by sha256 and the size of the file.
        4. 这有一张图，很清晰 https://github.com/google/go-containerregistry/tree/d7f8d06c87ed209507dd5f2d723267fe35b38a9f/pkg/v1/remote#anatomy-of-an-image-upload
    2. 所以，从registry直接拉下来的manifest里的内容，会和docker save导出的manifest的内容会有差异，体现在blobs/layer的tar包是否有gzip过
## Push manifest
1. PUT /v2/<name>/manifests/<reference>
