---
title: "[container] 1.容器基础之overlayfs"
date: 2025-03-03
categories : ["container"]
tags : ["container", "overlayfs"]
---

overlayfs ，如其名，覆盖文件系统，类似那些 overlay network一样（在underlay network上包一层），在原生的fs上包一层。  
overlayfs 是linux内核提供的功能，相关文档见 https://docs.kernel.org/filesystems/overlayfs.html  
容器使用 overlayfs 作为容器的文件系统，比如镜像是按层构建的，每一层都是lowerdir, 并创建一个容器的upperdir, 最终得到用户看到的容器文件系统。

# 使用
学习一个东西的方法，先看怎么使用，跑个demo出来，才不会言之无物。  

查看内核是否支持overlayfs
```
(base) liweiming@DESKTOP-4IDR6UQ:~/code/wymli.github.io$ grep overlay /proc/filesystems
nodev   overlay
```
这里的 `nodev` （no device）表示 overlayfs是一个`虚拟`文件系统，无需基于物理的块设备(比如硬盘)

跑一下 mount 指令
```
mkdir -p {lower,upper,work,merged}
mount -t overlay overlay_lwm -o lowerdir=lower,upperdir=upper,workdir=work merged
```
指令也比较好懂， `mount -t ${fs_type} ${fs_name} -o ... ${dest}` , -o 后面的是overlayfs相关的options  
overlayfs 的设计上，有四个文件夹，各自含义如下：
- lower: 只读的下层文件夹
- upper: 可写的上层文件夹
- work: 可以理解为tmp目录，用以完成overlay内部的一些操作，主要是为了操作的原子性， 防止操作在一半时突然断电，影响overlayfs的完整性。具体例子可以看后面COW。
- merged: 最终视图文件夹，提供给使用方

道理很好懂，merged文件夹时lower+upper的merge视图，包含两边的所有文件，其中lower层只读，以便于在多个容器中复用，upper层就是每个容器专有。

自己随便创建几个文件可以看到，在lowerdir 、upperdir创建的文件都会出现merged dir，在mergeddir删除的文件，会影响upperdir, 但不会影响lowerdir


# 特性
- 读文件：读到的是lowerdir + upperdir 的合并视图
- 写文件：当写只读层的lowerdir里的文件时, 会先copy文件到upperdir, 也就是有一步的COW(copy-on-write)，实际上会先copy到workdir, 然后rename到upperdir，可以认为copy是非原子的，但是rename是原子的，用workdir来完成原子操作
- 删文件: 当删只读层的lowerdir里的文件时，会在upperdir创建一个root用户下的同名空文件（这一步，网上的文档(比如大模型)一般是说会创建 .wh.${name} 文件，用以标识文件删除）
    - 不过官方文档还是比较清楚的:`A whiteout is created as a character device with 0/0 device number or as a zero-size regular file with the xattr "trusted.overlay.whiteout".`  
    这里我在mergedir删除lowerdir的文件后，可以在upperdir看到如下的新生成文件，对应 设备号为0(设备类型), 0(同一设备的某个具体实例)的字符设备文件  
    这里a显示0, 0, 因为a是字符设备，所以显示设备号。x是regular file，对应的那栏显示文件大小 2 byte.
    ```
    c--------- 2 root      root      0, 0 Mar  3 19:50 a
    -rw-r--r-- 1 liweiming liweiming    2 Mar  3 20:08 x
    ```
    > 这里可以在回顾一下文件类型：
    > - d: 代表目录
    > - c: 字符设备(比如终端 /dev/tty, 键盘鼠标啥的，按字节流访问)
    > - b: 块设备(比如硬盘，一次能访问一大块字节)
    > - -: 普通文件(regular file)  

