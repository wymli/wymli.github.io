---
title: "[distribute] 单应用分布式架构"
date: 2022-04-28
categories: ["distribute"]
tags: ["distribute"]
---

# Intro
对大部分的业务系统来说，分布式往往体现在微服务上，即多个服务之间的分布式网络调用。  

但是在分布式计算、分布式训练等特定领域，是需要真正的借助分布式机器进行并行计算或训练的，这一类应用也有几个经典的架构，或者说启动方式。

# 架构（启动方式）

## 无常驻服务节点管理进程
就像正常的非服务类应用一样，你要运行就直接启动它。在分布式领域，通常各个节点进程的角色是不同的，比如会区分master和slave（worker）。  
在设计上，一般通过传入命令行参数的形式区分是master还是worker，并在代码里针对不同的角色运行不同的代码。当然，如果逻辑复杂，也可以独立出来专门的master应用和worker应用。

比如，tensorflow的分布式计算就是典型的这类架构，通常通过在不同的机器上启动同一份py脚本，给这个脚本传入所有分布式节点的地址和本机的角色。

## 有专门的常驻服务节点管理进程
简单来说，就是在各个节点上运行node manager，管理这个机器。我们要提交训练或计算任务，就像专门的api server提交，api server转发给node manager。这里api server和node manager其实也是master/worker的关系。  

前面的自己启动进程是非常粗糙的，要每次手动在所有机器上启动，还要传入节点地址等信息，容易出错。引入节点管理进程后，我们只需要提交任务即可，不需要管理机器了。并且，这一类节点管理应用会帮忙调度，不再是像前面自己启动时写死机器节点了。  

比如，spark standalone就是这样的结构，想要运行spark分布式计算任务时，首先要搭建spark集群，spark standalone就是一类spark 集群，它通过首先在各个节点手动运行节点管理进程（master和worker），然后在任一机器上通过spark-submit.sh脚本提交spark任务，对应的被调度到的node manager就会启动相应的进程。

## 有泛化的常驻服务节点管理进程
前面的spark standalone只适用于spark，如果每个这种分布式应用都搭建一个node manager也麻烦，于是yarn出现了。yarn是一种hadoop集群内的资源调度器，原生支持大数据生态的分布式应用，通过自定义编写app master应用，也可以支持用户自己的分布式应用。  

在yarn里面，同样的，也是先在各个节点机器上启动yarn的node manager（worker）和api server（master）。为了解决不同应用的调度问题，yarn使用一种名叫application master的概念，所谓的application master就是对应具体应用的管理者，完成对具体应用的调度工作，是用户自己编写的，可以认为就是一种用户编写的yarn客户端，相当于k8s里的operator。yarn原生集成了spark，flink等的app master。  

要了解更多的信息，去了解 yarn client。