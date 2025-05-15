---
title: "[airflow] temporal"
date: 2025-05-08
categories : ["workflow"]
tags : ["workflow", "temporal"]
---

> 原文记录在飞书文档: https://c6t4wbgxht.feishu.cn/docx/MQmod4xkdoZ2TlxDbQncyQG9nbg


# 简单介绍
学习一个新的东西首先在搜索引擎上搜下，了解下大概是什么东西。如果直接看官网文档的话，有些假大空的不说人话，容易懵。但深入的话，还是要看官方文档和源码。

temporal是一个工作流引擎，和airflow类似。
先说术语：
- workflow：也就是dag，一个执行图
- activity：最小执行单元，也就是图节点
Temporal 和airflow类似，都使用编程语言定义workflow，而不是静态描述。

# workflow的执行：
1. 通过sdk向server发起workflow的执行
2. 自己启动worker（worker的代码内容比较固定，框架给了一套固定的写法），但是需要自己解决worker启动多少个、在哪里运行（裸进程、docker、k8s pod...），也就是自己全面接管数据面，控制面的temporal 负责下发任务，很灵活，不依赖任何编排引擎（yarn/k8s）
  1. worker需要配置任务队列、workflow名、activity名，一个workflow实例只能绑定一个队列，但可以处理多个workflow/activity
  2. 想要多个worker实例，就自己多线程或者多进程
  3. 由于workflow/activity的实现在编译期确定了，有修改或者新增时，需要重启worker（相比之下，airflow分发的是python文件，改完之后自动加载）


一个最简单的workflow运行如下：
`
func MyWorkflow(ctx workflow.Context, input string) error {
    var result stringerr := workflow.ExecuteActivity(ctx, MyActivity, input).Get(ctx, &result)
    return err
}


func MyActivity(ctx context.Context, input string) error {
    // 实现 Activity 的逻辑
    return nil
}
`
# 启动worker:
- worker要注册对应的workflow和activity，所以很明显，这个worker专为执行这个workflow而启动
`
func main() {
    // 创建 Worker
    w := worker.New(c, "my-worker", worker.Options{})
    // 注册 Workflow
    w.RegisterWorkflow(MyWorkflow)
    w.RegisterActivity(MyActivity)
    // 启动 Worker
    err := w.Run(worker.InterruptCh())
    if err != nil {
        log.Fatalln("Unable to start worker", err)
    }
}
`
# 启动workflow：
`
func main() {c, err := utils.NewTemporalClient(context.Background(), "default")if err != nil {
    log.Fatalln("Unable to create client", err)}
    defer c.Close()
    // 启动 Workflow
    err = c.ExecuteWorkflow(context.Background(), MyWorkflow, "input")
    if err != nil {
        log.Fatalln("Unable to start workflow", err)
    }
}
`

这种自己启动worker的架构可能和temporal用于云上有关，worker需要占用客户自己的资源，所以客户自己启动，cloud temporal service只负责控制面，其他数据面都交给用户。

# 训练任务调度
比如在训练任务调度领域，需要处理一个dag的反复执行（或者称之为工作流的递归）（也就是对每天的样本自动训练），在temporal中应该如何编写呢？（在airflow中，可以在dag的末节点增加一个对当前dag的触发。airflow支持一个dag定义同时执行多个dag实例）
和airflow类似，只要runID或者叫workflowID不同就行。




