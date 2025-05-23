---
title: "[tensorflow-arch] 入门"
date: 2022-04-10
categories: ["Tensorflow"]
tags: ["Tensorflow"]
---

# tensorflow入门
## intro
- tensorflow采用基于数据流图的模型设计方法。
- 基础平台层软件设计模式： 库模式和框架模式。库模式下，平台层软件以静态和动态的开发库存在，主程序(main)入口和控制流程掌握在用户手中，比如pytorch，numpy，tensorflow。框架模式下，平台层软件以可执行文件的形式存在，以后端守护进程独立运行，程序的入口和整体流程由框架控制，比如spark，mapreduce。
- tensorflow的计算核心是c++代码，称为运行时核心库，典型的是通过pip安装tensorflow后部署到site-packages的动态链接库文件，包括三个模块：分布式运行时，公共运行时，算子核函数。核心库的外层就是各个语言的API。
  - 公共运行时：实现数据流图计算的基本逻辑
  - 分布式运行：在公共运行时的基础上实现数据流图的跨进程协同计算逻辑
  - 算子核函数：包含图上具体操作节点的算法实现代码

- python包管理工具
  - anaconda
  - pip
  - virtualenv
- python软件发布的新格式是wheel（whl），用于取代过时的egg包格式。
- CUDA：Compute Unified Device Architecture

- 数据流图的编程范式是声明式编程，与之相比的是结构化编程，面向对象编程
- 数据流图被定义为用节点和有向边描述数学运算的有向无环图
  - 数据流图中的节点通常是各类操作（operation），比如数学运算，数据填充，结果输出，变量读写等，每个节点上的操作都需要分配具体的物理设备以确定在哪里计算（CPU，GPU等）
  - 数据流图中的有向边描述了节点间的输入输出关系，边上流动的是代表高维数据的张量，故命名为TensorFlow
- 基于梯度下降法优化求解的机器学习问题，分为两个计算阶段：
  - 前向图求值
    - 用户编写代码完成，包括定义模型的目标函数，损失函数，输入输出数据的形状和数据类型等
  - 后向图求梯度
    - 由TensorFlow的优化器自动生成，主要功能是计算模型参数的梯度值，并用梯度值高性对应的模型参数。

- 数据流图的主要概念
  - 节点：
    - 前向图中的节点统一称为操作，根据功能分为三类
      - 计算节点（Operation类）：无状态的计算或控制操作，数学函数或表达式，比如MatMul，BiasAdd，SoftMax，大多数节点都是这种类型。
        - 计算节点不需要显式构造Operation实例，一般都通过tf提供的各种操作函数，比如add，multiply等
      - 存储节点（Variable类）：有状态的变量操作，存储模型参数的变量，比如ReLu Layer的权重参数W和偏差b
        - 变量节点不是一个简单的节点，而是多个子节点构成的子图，通常由四个子节点构成：
          - 变量初始值（Initial Value）：无状态操作
          - 更新变量值的操作（Assign）：无状态操作
          - 读取变量值的操作（Read）：无状态操作
          - 变量操作：有状态操作，实际就是变量存储的实体，数据存在这个节点
      - 数据节点（Placeholder类）：占位符，比如Input和Label，用来描述输入输出的形状和类型，在执行时，占位符要填充对应的数据。
        - 在实际执行时，需要将数据填充（feed）到数据节点，比如sess.run(y,feed_dict{x:rand_array})，通过feed_dict传入。这里run的第一个参数代表要取出的变量的值（要计算的变量的值，会打印在stdout）
    - 后向图中的节点也分为三类：
      - 梯度值：经过前向图计算得出的模型参数的梯度
      - 更新模型参数的操作：定义了如何将梯度值更新到对应的模型参数
      - 更新后的模型参数：与前向图中的模型参数一一对应，但却是更新后的参数值，用于模型的下一轮训练
    - 前向图和后向图唯一的连接就是梯度，前向图根据模型参数和输入数据前向计算得到梯度，后向图通过梯度更新得到新的模型参数
  - 有向边
    - 数据流图中的有向边用于定义操作之间的关系，分为两类
      - 数据边：传输数据，绝大多数流动着张量的边都是这类
      - 控制边：定义控制依赖，通过设置节点的前置依赖来决定相关节点的执行顺序
  - 所有的节点都通过数据边或控制边连接，入度为0的节点没有前置依赖，可以立即执行；反之要等待前置依赖的系欸但执行结束后才能执行。
- 数据流图的执行顺序由库决定，与用户定义顺序无关，与节点之间的逻辑依赖关系和运行时库的实现机制有关
  - 数据流图上的节点执行顺序的实现借鉴了拓扑排序的设计思想：
    - 创建一个map存储节点和入度的映射，创建一个入度为0的节点的待执行队列
    - 扫描map，将入度为0的节点入队
    - 执行，并将执行完的节点的出度节点的入度减1
    - 重新扫描map，将入度为0的节点入队并执行，并将出度节点的入度递减，不断重复
- TensorFlow中的数据载体是张量，用张量统一表示所有数据，分为Tensor和SparseTensor（解决高维稀疏数据的内存占用）
- 张量的阶代表所描述数据的最大维度，是描述数据在高维空间的维数。定义每一阶的长度的可以唯一确定一个张量的形状。
  - 0阶张量：标量
  - 1阶张量：向量
  - 2阶张量：矩阵
  - 3阶张量：...
- 张量在数据定义上是一个句柄，存储张量的元信息和指向数据的指针，而不实际存储数据，这是为了实现嗯内存复用，一个前置操作的输出值被输入到多个后置操作时，无需重复存储多个输出值。当张量不再被引用后，内存将被释放，通过引用计数，就像GC一样。
- 构造张量的参数，也就是张量的属性，即`t1=Tensor(dtype,shape,graph,...)`
  - dtype：张量传输数据的类型
  - shape：张量传输数据的形状
  - graph：张量所属的数据流图
  - name： 张量在数据流图中的名字
  - op：   生成该张量的前置操作
  - value_index：张量在该前置操作的所有输出值中的索引
- 一般情况，不需要使用`Tensor()`来构造张量，可以通过更高级的API或通过操作（比如add）来间接创建张量
  - a = tf.constant(1.0)
  - b = tf.add(a,a)
- 会话Session：就是真正执行数据流图计算的上下文，需要create，run，close。在tf2.0中，删除了Session。
  - TensorFlow 1.X需要用户使用tf.*里的API手动构建计算图。然后用session.run()传入输入tensor并且计算某些输出tensor。TensorFlow 2.X默认是Eager执行模式，我们在定义一个Operation的时候会动态构造计算图并且马上计算。
  - 这样的好处就是我们的代码就像在执行普通的Python代码，Graph和Session等实现细节概念都被隐藏在后面了。
  - Eager执行的另外一个好处就是不再需要tf.control_dependencies了(如果不知道也没有关系，以后不会再用到了)，因为Tensorflow的计算图是按照Python代码的顺序执行。

- 优化器：为用户实现了自动计算模型参数梯度值的功能。tf的优化器根据前向图的计算拓扑和损失值，利用链式求导法则依次求出每个模型参数在给定数据下的梯度值，并将其更新到对应的模型参数以完成一个训练步骤。优化器是tf的训练工具。
  - 优化器自动生成后向图，即gradients子图


## 分布式架构
> 分布式训练分为`PS-worker`架构和`Ring-allreduce`架构，前者是中心化非对称的，后者是去中心化对称的全worker架构

- 这种架构不是C/S架构，而是类似于SPARK，只是将单进程变成多进程在多个服务器运行而已。对于Spark，yarn或原生的spark-standalone提供了集群管理，让你可以一键在多机构建多进程任务，所以非常类似于C/S架构了，但不管怎么说，他其实只是集群的节点管理器帮你启动进程而已。对于tf来说，也是一样，不过tf目前来说没有实现集群节点管理，都是手动在多机启动进程，通过在同一份代码里预置PS和worker的操作，并在启动进程时指明是PS还是worker
- 计算形态：
  - 推理态：只前向计算
  - 训练态：执行前向图的推理计算和后向图的梯度计算参数更新
- 分布式架构：PS-Worker，解决了大规模参数在分布式存储和更新时的一致性问题
  - 模型的所有参数唯一的存储在PS的内存中，当参数过大时，就分布式的存在多个PS中
  - 模型训练过程中的计算（包括前向图推理和后向图梯度计算）都由worker完成
    - 不同的worker的数据流图都是相同的，只是填充的数据不同，从而数据并行
  - 训练数据一般存储在分布式文件系统中，比如hdfs
- 分布式模型的单步训练过程：
  1. worker从PS拉取模型参数，各worker拉取的参数一样
  2. worker从hdfs读取不同批次的批数据，各worker读取的数据不同
  3. worker执行前向图计算和后向图计算梯度
  4. worker将梯度推送到PS上
  5. PS汇总梯度，求出梯度的均值，并更新模型参数
- PS-worker架构的思想是分离模型和训练，PS负责模型参数的存储、分发、汇总、更新；Worker负责推理计算和梯度计算。
- 分布式训练一般采用数据并行加速模型训练
  - 数据并行分为两类：
    - 图内复制（in-graph replication）：单进程内的数据并行，即单机多卡，对应pytorch的`dp`
    - 图间复制（between-graph replication）：多进程，跨机器分布式训练
  - 参数更新机制：
    - 异步训练（asynchronous training）：每个worker独立训练，计算出梯度后按照一定策略等待特定时间发生后进行模型参数更新，也可以直接立即更新，主要看异步更新策略，而不需要等待其他worker完成训练计算梯度
    - 同步训练（synchronous training）：每个worker独立训练计算梯度上报梯度并等待从PS拉取最新的模型参数，PS会等待所有worker计算完后再汇总更新模型参数，计算快的worker要等待慢worker计算
  - 同步训练比异步训练收敛速度快，训练步数少。异步训练单步快，但容易受单批数据的影响，训练步数多。
- 同步训练机制：
  - 副本是模型训练过程中单独处理一份批数局的抽象
    - 并行副本数：单步训练中用户希望的并行数据个数
    - 实际副本数：单步训练中实际参与计算的worker数
    - 如果并行副本数大于实际副本数，代表计算快的worker会单步计算多个批次；如果小于，则代表个别worker不需要训练
  - 同步优化器，以M个模型参数，N个并行副本数为例
    - 梯度聚合器：存储梯度值的队列，有多少个模型参数就有多少个梯度队列。对于每个模型参数，都存在一个长度为N的梯度队列，共M个队列
    - 同步标记队列：存储同步标记的队列，全局一条队列。同步标记决定worker是否能够参与梯度计算，有多少个并行副本数队列就有多少个同步标记，只有拿到同步标记的worker才能拿到最新的模型参数。这个同步标记（sync token）实际是一个表示global_step全局训练步数（第几步）的值。worker会首先拿到该代表全局训练步数的token，更新自己的本地训练步数，然后从PS获取最新的模型参数，计算梯度。
    - 每一次上报的梯度和下发的模型参数都会附带训练步数的字段，以保证不会串数据。对于PS来说，梯度聚合器在收集梯度时会校验收到的梯度的训练步数是不是当前的全局训练步数（版本号的作用），否则丢弃。Worker上传完梯度后，会去阻塞的领取同步标记队列中的标记，由于已经领完，只能等待全局进入下一步训练（如果是能者多劳，并行副本数大于实际副本数，那么快worker能在同步标记队列中领到标记，并继续计算）。PS更新完参数后，会更新全局训练步数+1，并按并行副本数入队同步标记队列。
- 异步训练机制：
  - 每个worker计算出的梯度值上报后，PS更新参数
  - 不同的worker进行参数的拉取和更新时，tf内部的锁机制保证模型参数的数据一致性
  - 异步训练的一个典型问题就是次优解，比如worker1和worker2同时拉取参数，计算，worker1先上报更新参数，比如是向左的梯度，然后worker2上报，也是向左的梯度，但此时参数已经更新过了，导致两次向左，可能就向左过头了

## TensorFlow Serving
- 生产系统中，模型以推理态运行，我们需要打通模型训练到发布的全流程
- 
