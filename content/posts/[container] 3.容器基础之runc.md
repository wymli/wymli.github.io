---
title: "[container] 3.容器基础之runc"
date: 2025-03-04
categories : ["container"]
tags : ["container", "oci", "runc"]
---

如果没有安装runc，先安装 (如果你安装了dockerd/containerd，一般不用再单独安装)
```
wget https://github.com/opencontainers/runc/releases/download/v1.2.5/runc.amd64 -O runc && chmod +x runc
```

# 制作 bundle
安装oci runtime spec, 我们先制作oci runtime bundle，也就是config.json 和 rootfs

## rootfs
一般rootfs不是从零开始制作的，直接用现有的镜像
1. 可以直接使用ctr mount 指令将镜像mount到某个目录
2. 可以使用 docker export 指令导出一个这在运行的容器的rootfs tar包
3. 可以使用 docker save 指令导出一个镜像的oci tar包，然后逐个解压blobs目录下的每个layer的tar包
```
docker run -d python:3.13 sleep 1d
docker export aaa4edf37e57 -o python-3.13.tar
mkdir rootfs && tar -xvf python-3.13.tar -C rootfs
```
如此，rootfs已经被准备好
> 在这一步，也可以通过ctr mount 指令，直接mount镜像到某个目录，无需上面这么复杂

## config.json 
生成默认的config.json (rootless container)
```
runc spec --rootless
```
啥也不用改，直接run，就能以当前目录下的config.json + rootfs 启动一个名为test的容器
```
runc run test
```

## 修改overlayfs
我们希望能在原有的python镜像的基础上，hack进一些ssh的相关工具
```
mv rootfs lowerdir
mkdir rootfs
sudo mount -t overlay test -o lowerdir=lowerdir,upperdir=uppe
rdir,workdir=workdir rootfs
```
- 注意修改一下config.json里的rootfs.readonly, 改为false

随后可以直接用runc直接启动, 在根目录创建一个文件试试
```
runc run test 
# echo "hello world" > /test
```
退出容器后可以看到，lowerdir无变更，upperdir有变更

> 基于此，在一些需要持久化存储的场景，可以把容器的upperdir放在ebs上


## 添加sshd
https://github.com/opencontainers/runc/issues/2517#issuecomment-720897616
```
在容器里安装 openssh-server 即可，安装的内容将在upperdir中
```