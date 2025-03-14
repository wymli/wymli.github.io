---
title: "[container] 2.容器基础之oci runtime"
date: 2025-03-03
categories : ["container"]
tags : ["container", "oci"]
---

oci(open container initiative, 开放容器倡议) 主要有三个大的spec, runtime（容器运行时）、image（镜像）、distribution（分发）

# OCI Runtime Spec
包含三方面：配置和打包定义（也就是bundle和config.json的schema）、执行环境、容器生命周期及相关操作
> 对于 oci runtime spec，有较多实现，比如各个语言的容器实现，比如runc、crun, 也有vm实现，比如kata

## container bundle 容器打包
容器打包后，可以被运行时消费进而运行容器，所以这里定义了打包的规则：
1. bundle 包含 1. config.json 2. rootfs
2. bundle.tar 解压后直接就是 bundle files, 没有嵌套的一层根目录

执行runc spec, 将会生成如下的config.json
```
{
        "ociVersion": "1.0.2-dev", // schema版本，一个良好的设计，一定要一个版本字段，用来应对可能的schema不兼容改动
        "process": { // 容器主进程相关的配置
                "terminal": true, // 类似 docker run -t
                "user": {
                        "uid": 0,
                        "gid": 0
                },
                "args": [
                        "sh"
                ],
                "env": [
                        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                        "TERM=xterm"
                ],
                "cwd": "/", // working directory
                "capabilities": {
                        "bounding": [ // 进程及子进程可以使用的全部能力
                                "CAP_AUDIT_WRITE",
                                "CAP_KILL",
                                "CAP_NET_BIND_SERVICE"
                        ],
                        "effective": [ // 进程已经生效的实际能力
                                "CAP_AUDIT_WRITE",
                                "CAP_KILL",
                                "CAP_NET_BIND_SERVICE"
                        ],
                        "permitted": [ // 进程可以使用的全部能力，进程主动激活后成为effective capabilities
                                "CAP_AUDIT_WRITE",
                                "CAP_KILL",
                                "CAP_NET_BIND_SERVICE"
                        ],
                        "ambient": [ // 子进程继承的能力
                                "CAP_AUDIT_WRITE",
                                "CAP_KILL",
                                "CAP_NET_BIND_SERVICE"
                        ]
                },
                "rlimits": [
                        {
                                "type": "RLIMIT_NOFILE", // 限制打开文件数 number of file
                                "hard": 1024,
                                "soft": 1024
                        }
                ],
                "noNewPrivileges": true // 禁止容器进程新增权限
        },
        "root": {
                "path": "rootfs",
                "readonly": true
        },
        "hostname": "runc",
        "mounts": [
                {
                        "destination": "/proc",
                        "type": "proc",
                        "source": "proc"
                },
                {
                        "destination": "/dev",
                        "type": "tmpfs",
                        "source": "tmpfs",
                        "options": [
                                "nosuid",
                                "strictatime",
                                "mode=755",
                                "size=65536k"
                        ]
                },
                {
                        "destination": "/dev/pts",
                        "type": "devpts",
                        "source": "devpts",
                        "options": [
                                "nosuid",
                                "noexec",
                                "newinstance",
                                "ptmxmode=0666",
                                "mode=0620",
                                "gid=5"
                        ]
                },
                {
                        "destination": "/dev/shm",
                        "type": "tmpfs",
                        "source": "shm",
                        "options": [
                                "nosuid",
                                "noexec",
                                "nodev",
                                "mode=1777",
                                "size=65536k"
                        ]
                },
                {
                        "destination": "/dev/mqueue",
                        "type": "mqueue",
                        "source": "mqueue",
                        "options": [
                                "nosuid",
                                "noexec",
                                "nodev"
                        ]
                },
                {
                        "destination": "/sys",
                        "type": "sysfs",
                        "source": "sysfs",
                        "options": [
                                "nosuid",
                                "noexec",
                                "nodev",
                                "ro"
                        ]
                },
                {
                        "destination": "/sys/fs/cgroup",
                        "type": "cgroup",
                        "source": "cgroup",
                        "options": [
                                "nosuid",
                                "noexec",
                                "nodev",
                                "relatime",
                                "ro"
                        ]
                }
        ],
        "linux": {
                "resources": {
                        "devices": [
                                {
                                        "allow": false,
                                        "access": "rwm"
                                }
                        ]
                },
                "namespaces": [ // 表示容器是否新建下面的namespace
                        {
                                "type": "pid"
                        },
                        {
                                "type": "network"
                        },
                        {
                                "type": "ipc"
                        },
                        {
                                "type": "uts"
                        },
                        {
                                "type": "mount"
                        }
                ],
                "maskedPaths": [
                        "/proc/acpi",
                        "/proc/asound",
                        "/proc/kcore",
                        "/proc/keys",
                        "/proc/latency_stats",
                        "/proc/timer_list",
                        "/proc/timer_stats",
                        "/proc/sched_debug",
                        "/sys/firmware",
                        "/proc/scsi"
                ],
                "readonlyPaths": [
                        "/proc/bus",
                        "/proc/fs",
                        "/proc/irq",
                        "/proc/sys",
                        "/proc/sysrq-trigger"
                ]
        }
}
```