---
title: "[install] wsl 和 containerd 环境准备踩坑"
date: 2025-03-03
categories : ["install"]
tags : ["wsl", "containerd"]
---

后面开始用家里的windows主机开发和学习，换了新环境，配置环境很折磨，wsl虽说很方便，但是遇到各种坑，解决起来很费脑

# wsl2 配置
2025年wsl已经有了很多新的演进，在网络方便进步很多，原来wsl1如果要连接宿主机的代理，需要配宿主机的ip，但是宿主机的ip不固定，比较麻烦（不过也就是一个脚本的事，问题也不大）  
wsl2支持镜像网络模式，wsl和host可以共用网络地址了，也就是wsl里可以通过localhost访问host。  
配置如下，在windows的用户目录下创建 `.wslconfig`
```
PS C:\Users\liweiming> cat .\.wslconfig
[wsl2]
networkingMode=mirrored
dnsTunneling=true
firewall=true
autoProxy=true

[experimental]
# requires dnsTunneling but are also OPTIONAL
bestEffortDnsParsing=true
```
然后重启 wsl  
然后在wsl配置代理即可（这一步卡了很久，网上的文档都没有这一步，可能是我电脑的原因，反正windows的代理没自动生效到wsl上）：
```
export http_proxy="http://localhost:7890"
export https_proxy="http://localhost:7890"
```

# VSCode 与 wsl
在wsl中尝试用 `code .` 的方式打开vscode，结果报错 `Command 'code' not found`， 看了下$PATH, 好家伙，`/mnt/c/Users/liweiming/AppData/Local/Programs/Microsoft:Code/bin`， 反正也不知道是哪一步错了，windows路径里的空格在linux都变成了`:`，不过也好解决，自己加下$PATH就好  
配置如下:
```
export PATH="/mnt/c/Users/liweiming/AppData/Local/Programs/Microsoft VS Code/bin":$PATH
```

# rootless containerd 安装
下载最新的nerdctl
```
wget https://github.com/containerd/nerdctl/releases/download/v2.0.3/nerdctl-2.0.3-linux-amd64.tar.gz

bash /nerdctl/extras/rootless/containerd-rootless-setuptool.sh install 
```
这一步一直报错 `Failed to start containerd.service: Unit dbus.socket not found.`

卡了较久，最后在文档https://rootlesscontaine.rs/getting-started/common/login/，找到要安装 user模式的 dbus
```
systemctl --user is-active dbus
sudo apt-get install -y dbus-user-session
systemctl --user start dbus
```
随后再执行一遍 `bash /nerdctl/extras/rootless/containerd-rootless-setuptool.sh install` 即可

验证下安装：
```
(base) liweiming@DESKTOP-4IDR6UQ:~$ nerdctl run hello-world:latest
docker.io/library/hello-world:latest:                                             resolved       |++++++++++++++++++++++++++++++++++++++|
index-sha256:bfbb0cc14f13f9ed1ae86abc2b9f11181dc50d779807ed3a3c5e55a6936dbdd5:    done           |++++++++++++++++++++++++++++++++++++++|
manifest-sha256:03b62250a3cb1abd125271d393fc08bf0cc713391eda6b57c02d1ef85efcc25c: done           |++++++++++++++++++++++++++++++++++++++|
config-sha256:74cc54e27dc41bb10dc4b2226072d469509f2f22f1a3ce74f4a59661a1d44602:   done           |++++++++++++++++++++++++++++++++++++++|
layer-sha256:e6590344b1a5dc518829d6ea1524fc12f8bcd14ee9a02aa6ad8360cce3a9a9e9:    done           |++++++++++++++++++++++++++++++++++++++|
elapsed: 7.2 s                                                                    total:  13.4 K (1.9 KiB/s)


Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```