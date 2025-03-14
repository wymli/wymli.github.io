---
title: "[container] 4.容器基础之oci image"
date: 2025-03-06
categories : ["container"]
tags : ["container", "oci"]
---

描述了一个镜像的打包目录和相关文件的schema

# 目录结构
利用docker save拿到一个docke 镜像的tar包，解包后得到如下目录，这是一个兼容oci image spec的目录（但也只是兼容，不是严格相等，里面有一些oci image spec里未定义的文件）
```
.
├── blobs // Contains content-addressable blobs, 以文件的hash值作为文件名，内容可能是json或者是tar包等，是oci image的data层
│   └── sha256
│       ├── 01c9a2a5f23727d0aab91da9d479286e25780d50b574f1a9df47ca850a88b591
│       ├── 20a9b386e10e3498e69df416a8399580266c8a1a5e9b61499dad040b6adf389d
│       ├── 36d17f72f4f3630dbc93a0b2fe6f7e61179c597cbef32f815b34f70ef1e402f2
│       ├── 4571159699acacba5c116a51948bf915c1ddd4e948835281959a4057d9585ea5
│       ├── 462728c2d5e8545bccb55245c5b1894e2b38f433e7c626b9decfa0d8c450c7f0
│       ├── 4b017a36fd9c6bc8b31d2435fd4542fadb6ff333f58089e13fdae0c9c32521ba
│       ├── 6a2f4c46fde663a8ba77d90d5c03cce66bb73ab86420ef4d7601dd4efbc8e8df
│       ├── 75c81d4302970814333f1d90f05991d1d41e3eb6ff685022f8daaf7d3b8d9b55
│       ├── 93bc0edf8c04050dd64e3167e6f61e947f95eba2015fc2a52681edc949f32494
│       ├── b200d32a35f55dcf1abbe58c3853d03ad3ae426768930e15c862e778831acd82
│       ├── c11894706a24d6c86caa0ed1dcd3c12ba4ea829b92f90e4d3693e803f1fdc696
│       ├── c3d5e3eb8c7ece0139d56c6e321f2d4f42ced54469d8b77439b1221c61a05e51
│       ├── c7833e0541d97c713cc25f793288fe745fbadb35e28662f095898772796d02b3
│       ├── f8217d7865d28a53786a3f9ccb3760a59500fba32d367b1fe99470f974a6a669
│       ├── f911087b1237b68bf2fde6931af826d83fbcad04b37c6df2eee0fc1560e7f655
│       ├── fb8d481c6b59d23edcf9529bfd9683a62245ec7adb22fb6307e04d0293eab4e0
|
├── index.json // 索引，是oci image的入口，里面定义了manifest.json的hash值（随后可以在blobs里找到），是oci image的meta层
├── manifest.json // docker的manifest.json, 不是oci image 规范，其内容和blobs/manifest.json 有区别
├── oci-layout // 内容是镜像布局版本
└── repositories // docker 特有
```


## blobs
blobs里主要有三类文件：
1. manifest.json 
    1. 里面定义每一层的digest + config.json 的digest （由于contenet-addressable, digest就是文件名）
2. config.json
    1. 里面定义了一些元数据，比如镜像的env、cmd、构建历史（docker history 命令）等
    2. 构建 oci runtime spec时，config.json 会基于这个config进行渲染
3. layer tarball
    1. 每一层的文件tar打包，unpack后就是该层新增的一些文件(注意出于效率考虑，并没有压缩)

## manifest.json
一个典型的manifest.json如下，里面包含了config文件和layers文件列表，简单来说，config文件用于形成runtime的config.json，layers的tar包列表用于形成runtime的rootfs。
```
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": {
    "mediaType": "application/vnd.oci.image.config.v1+json",
    "digest": "sha256:36d17f72f4f3630dbc93a0b2fe6f7e61179c597cbef32f815b34f70ef1e402f2",
    "size": 6256
  },
  "layers": [
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar",
      "digest": "sha256:01c9a2a5f23727d0aab91da9d479286e25780d50b574f1a9df47ca850a88b591",
      "size": 121313280
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar",
      "digest": "sha256:f8217d7865d28a53786a3f9ccb3760a59500fba32d367b1fe99470f974a6a669",
      "size": 49581056
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar",
      "digest": "sha256:20a9b386e10e3498e69df416a8399580266c8a1a5e9b61499dad040b6adf389d",
      "size": 181902848
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar",
      "digest": "sha256:4b017a36fd9c6bc8b31d2435fd4542fadb6ff333f58089e13fdae0c9c32521ba",
      "size": 597108736
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar",
      "digest": "sha256:462728c2d5e8545bccb55245c5b1894e2b38f433e7c626b9decfa0d8c450c7f0",
      "size": 18359296
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar",
      "digest": "sha256:93bc0edf8c04050dd64e3167e6f61e947f95eba2015fc2a52681edc949f32494",
      "size": 72050688
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar",
      "digest": "sha256:fb8d481c6b59d23edcf9529bfd9683a62245ec7adb22fb6307e04d0293eab4e0",
      "size": 5120
    }
  ]
}
```
## config.json
一个典型的config.json 如下。  
值得注意的是里面的diff_ids, 里面记录了每一层tar包的哈希值(只是比较奇怪，为什么叫diff_id)
```
{
  "architecture": "amd64",
  "config": {
    "Env": [
      "PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      "GPG_KEY=7169605F62C751356D054A26A821E680E5FA6305",
      "PYTHON_VERSION=3.13.2",
      "PYTHON_SHA256=d984bcc57cd67caab26f7def42e523b1c015bbc5dc07836cf4f0b63fa159eb56"
    ],
    "Cmd": [
      "python3"
    ]
  },
  "created": "2025-02-04T23:51:20Z",
  "history": [
    {
      "created": "2023-05-10T23:29:59Z",
      "created_by": "# debian.sh --arch 'amd64' out/ 'bookworm' '@1740355200'",
      "comment": "debuerreotype 0.15"
    },
    {
      "created": "2023-05-10T23:29:59Z",
      "created_by": "RUN /bin/sh -c set -eux; \tapt-get update; \tapt-get install -y --no-install-recommends \t\tca-certificates \t\tcurl \t\tgnupg \t\tnetbase \t\tsq \t\twget \t; \trm -rf /var/lib/apt/lists/* # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2024-01-09T01:14:25Z",
      "created_by": "RUN /bin/sh -c set -eux; \tapt-get update; \tapt-get install -y --no-install-recommends \t\tgit \t\tmercurial \t\topenssh-client \t\tsubversion \t\t\t\tprocps \t; \trm -rf /var/lib/apt/lists/* # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2024-01-09T01:14:25Z",
      "created_by": "RUN /bin/sh -c set -ex; \tapt-get update; \tapt-get install -y --no-install-recommends \t\tautoconf \t\tautomake \t\tbzip2 \t\tdefault-libmysqlclient-dev \t\tdpkg-dev \t\tfile \t\tg++ \t\tgcc \t\timagemagick \t\tlibbz2-dev \t\tlibc6-dev \t\tlibcurl4-openssl-dev \t\tlibdb-dev \t\tlibevent-dev \t\tlibffi-dev \t\tlibgdbm-dev \t\tlibglib2.0-dev \t\tlibgmp-dev \t\tlibjpeg-dev \t\tlibkrb5-dev \t\tliblzma-dev \t\tlibmagickcore-dev \t\tlibmagickwand-dev \t\tlibmaxminddb-dev \t\tlibncurses5-dev \t\tlibncursesw5-dev \t\tlibpng-dev \t\tlibpq-dev \t\tlibreadline-dev \t\tlibsqlite3-dev \t\tlibssl-dev \t\tlibtool \t\tlibwebp-dev \t\tlibxml2-dev \t\tlibxslt-dev \t\tlibyaml-dev \t\tmake \t\tpatch \t\tunzip \t\txz-utils \t\tzlib1g-dev \t; \trm -rf /var/lib/apt/lists/* # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "RUN /bin/sh -c set -eux; \tapt-get update; \tapt-get install -y --no-install-recommends \t\tlibbluetooth-dev \t\ttk-dev \t\tuuid-dev \t; \trm -rf /var/lib/apt/lists/* # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "ENV GPG_KEY=7169605F62C751356D054A26A821E680E5FA6305",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "ENV PYTHON_VERSION=3.13.2",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "ENV PYTHON_SHA256=d984bcc57cd67caab26f7def42e523b1c015bbc5dc07836cf4f0b63fa159eb56",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "RUN /bin/sh -c set -eux; \t\twget -O python.tar.xz \"https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz\"; \techo \"$PYTHON_SHA256 *python.tar.xz\" | sha256sum -c -; \twget -O python.tar.xz.asc \"https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc\"; \tGNUPGHOME=\"$(mktemp -d)\"; export GNUPGHOME; \tgpg --batch --keyserver hkps://keys.openpgp.org --recv-keys \"$GPG_KEY\"; \tgpg --batch --verify python.tar.xz.asc python.tar.xz; \tgpgconf --kill all; \trm -rf \"$GNUPGHOME\" python.tar.xz.asc; \tmkdir -p /usr/src/python; \ttar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz; \trm python.tar.xz; \t\tcd /usr/src/python; \tgnuArch=\"$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)\"; \t./configure \t\t--build=\"$gnuArch\" \t\t--enable-loadable-sqlite-extensions \t\t--enable-optimizations \t\t--enable-option-checking=fatal \t\t--enable-shared \t\t--with-lto \t\t--with-ensurepip \t; \tnproc=\"$(nproc)\"; \tEXTRA_CFLAGS=\"$(dpkg-buildflags --get CFLAGS)\"; \tLDFLAGS=\"$(dpkg-buildflags --get LDFLAGS)\"; \t\tarch=\"$(dpkg --print-architecture)\"; arch=\"${arch##*-}\"; \t\tcase \"$arch\" in \t\t\tamd64|arm64) \t\t\t\tEXTRA_CFLAGS=\"${EXTRA_CFLAGS:-} -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer\"; \t\t\t\t;; \t\t\ti386) \t\t\t\t;; \t\t\t*) \t\t\t\tEXTRA_CFLAGS=\"${EXTRA_CFLAGS:-} -fno-omit-frame-pointer\"; \t\t\t\t;; \t\tesac; \tmake -j \"$nproc\" \t\t\"EXTRA_CFLAGS=${EXTRA_CFLAGS:-}\" \t\t\"LDFLAGS=${LDFLAGS:-}\" \t; \trm python; \tmake -j \"$nproc\" \t\t\"EXTRA_CFLAGS=${EXTRA_CFLAGS:-}\" \t\t\"LDFLAGS=${LDFLAGS:--Wl},-rpath='\\$\\$ORIGIN/../lib'\" \t\tpython \t; \tmake install; \t\tbin=\"$(readlink -ve /usr/local/bin/python3)\"; \tdir=\"$(dirname \"$bin\")\"; \tmkdir -p \"/usr/share/gdb/auto-load/$dir\"; \tcp -vL Tools/gdb/libpython.py \"/usr/share/gdb/auto-load/$bin-gdb.py\"; \t\tcd /; \trm -rf /usr/src/python; \t\tfind /usr/local -depth \t\t\\( \t\t\t\\( -type d -a \\( -name test -o -name tests -o -name idle_test \\) \\) \t\t\t-o \\( -type f -a \\( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \\) \\) \t\t\\) -exec rm -rf '{}' + \t; \t\tldconfig; \t\texport PYTHONDONTWRITEBYTECODE=1; \tpython3 --version; \tpip3 --version # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "RUN /bin/sh -c set -eux; \tfor src in idle3 pip3 pydoc3 python3 python3-config; do \t\tdst=\"$(echo \"$src\" | tr -d 3)\"; \t\t[ -s \"/usr/local/bin/$src\" ]; \t\t[ ! -e \"/usr/local/bin/$dst\" ]; \t\tln -svT \"$src\" \"/usr/local/bin/$dst\"; \tdone # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-02-04T23:51:20Z",
      "created_by": "CMD [\"python3\"]",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    }
  ],
  "os": "linux",
  "rootfs": {
    "type": "layers",
    "diff_ids": [
      "sha256:01c9a2a5f23727d0aab91da9d479286e25780d50b574f1a9df47ca850a88b591",
      "sha256:f8217d7865d28a53786a3f9ccb3760a59500fba32d367b1fe99470f974a6a669",
      "sha256:20a9b386e10e3498e69df416a8399580266c8a1a5e9b61499dad040b6adf389d",
      "sha256:4b017a36fd9c6bc8b31d2435fd4542fadb6ff333f58089e13fdae0c9c32521ba",
      "sha256:462728c2d5e8545bccb55245c5b1894e2b38f433e7c626b9decfa0d8c450c7f0",
      "sha256:93bc0edf8c04050dd64e3167e6f61e947f95eba2015fc2a52681edc949f32494",
      "sha256:fb8d481c6b59d23edcf9529bfd9683a62245ec7adb22fb6307e04d0293eab4e0"
    ]
  }
}
```

# docker build
dockerd在收到docker cli传过来的 build bundle后，是怎么一层一层构建镜像的呢？ 
    
其实很简单，首先`镜像是分层构建的，每一层构建完后，都打包层一个tar包`  
那么，每一层对应的那一条命令，是如何构建出来tar包的呢？也很简单，在前面将overlayfs的时候，已经知道，我们有lowerdir和upperdir，所以在构建每一层时，其实就是以之前所有层构建好的镜像（你可以理解为是一个临时镜像，但它是完备的镜像，因为dockerfile即使没有下一行命令，它也是完备的dockerfile）启动一个临时容器，执行新层的命令，新产出的文件将会在upperdir，进而可以被打包成tar包，如此循环。

# image bundle to runtime bundle
一个镜像bundle是如何转换成运行时bundle的呢？（这里的bundle就是一个文件目录树）  
- 对于rootfs，会按照manifest里定义的tar包列表按顺序解压。
    1. 这时候你会发现，有一些文件只在blobs里有，但manifest里没有，这些文件不会应用到runtime rootfs里，可能是一些注释文件啥的，比如Dockerfile里的COMMENT、MANINTAINER之类的。


# 容器运行时对image的处理
值得注意的是，oci image spec定义了一种标准的image存储格式，用于兼容不同的容器运行时，类似一种数据交换协议（比如json），但是在容器运行时内部，往往会用自己内部的方式存储image，比如对于containerd，所有的blobs存储在一个目录，所有的manifest存储在一个目录。  
OCI Image Spec 更像是一个 ​中间格式，用于在不同工具和平台之间传输和共享镜像。