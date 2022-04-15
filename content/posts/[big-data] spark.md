---
title: "[big-data] spark"
date: 2022-04-15
categories: ["big-data"]
tags: ["big-data"]
---


# Spark
- 并行计算框架
- 支持流式或批式
- spark提交有一个单独的spark-commit.sh脚本
- 批处理是spark core
- 流处理是spark streaming，这里的流在实现上是会传入一个窗口大小和下一个窗口的位移，来产生RDD，一个RDD就是一个窗口的小批次数据，所以spark streaming只是在批式spark core上包装了一下。

## 执行流程
一个spark 应用的流程是这样的：  
1. 创建sparkcontext类
```python
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
conf = SparkConf()
conf.setMaster("local").setAppName("My app") <- 这里master是local，表示本地模式，一般是local[N],表示N个线程。也可以是spark standalone或yarn
sc = SparkContext(conf=conf)
# 或直接 sc = SparkContext('local', 'my app')
```
2. sparkcontext实例调用各种数据输入方法，生成RDD。典型的数据输入是hdfs，格式是text，比如
```python
# 从hdfs读取textfile
lines = sc.textFile("hdfs://hadoop102:9000/fruit.txt")
print(lines.collect()) # rdd.collect(): Return a list that contains all of the elements in this RDD.
```
3. 执行transformation算子，这种算子的典型代表就是map，flatmap，filter，distinct，union，reduceByKey等
```python
from operator import add
res = lines.flatmap(lambda x: x.split(",")).map(lambda x: (x,1)).reduceByKey(add)
# rdd.flatmap: Return a new RDD by first applying a function to all elements of this RDD, and then flattening the results. 典型的例子就是将一行转成单词，最终从行的列表变成单词的列表。
# rdd.map: Return a new RDD by applying a function to each element of this RDD. 典型的例子就是将单词变成带计数，即apple => (apple, 1)
# rdd.reduceByKey: Merge the values for each key using an associative and commutative reduce function. 类似MR中的Combiner。这里reduceByKey需要传入的是针对相同key的reduce函数。所谓的key就是pair RDD中的第一个元素，即二元组x中的x[0]，换句话说，经过map后RDD自动变成了Pair RDD。而所谓的reduce函数的运行机制就是：将RDD的元素两两传入函数，返回一个新元素，并将新元素和下一个元素再一起两两传入函数，直到只剩下一个元素。 reduceByKey是Key范围内的reduce。计算机制和fold是一样的。
# 这里的operator.add 等价于 lambda a,b: a+b
```
4. 执行action算子，这种算子的典型代表是reduce,foreach，saveAsTextFile，collect，count，top等
```python
res.saveAsTextFile("hdfs://...")
sc.stop()
```
5. 执行action算子就意味提交job

## 名词解释
[cite](https://www.jianshu.com/p/3aa52ee3a802)
任务视角：
- Application：用户手写定义的应用，一个sparkcontext就是一个spark程序，用户编写的Spark应用程序,包括一个Driver和多个executors。
- Job：一个spark app包含一个或多个Job，每遇到一个RDD的Action操作就生成一个新的Job。
- Stage：一个Job分为一个或多个Stage，各个stage之间按照顺序执行。
- Task：Task是被分配到一个Executor上的计算单元， 一个Stage分为多个Task。Task执行相同的程序逻辑，只是它们操作的数据不同。一般RDD的一个Partition对应一个Task。Stage将划分成多个`可以并行计算的`Task。

进程：
- Driver: 运行main()函数并创建SparkContext进程。比如由driver进程执行top函数进行内存排序
- Executor：运行在worker node上执行具体的计算任务，存储数据的进程

数据视角：
- RDD -> partition -> record.   Partition是Spark进行数据处理的基本单位，一般来说一个Partition对应一个Task，而一个Partition中通常包含数据集中的多条记录(Record)，一个RDD包括多个Partition。

### 宽窄依赖
Spark中RDD的高效与DAG（有向无环图）有很大的关系，在DAG调度中需要对计算的过程划分Stage，划分的依据就是RDD之间的依赖关系。RDD之间的依赖关系分为两种，宽依赖(wide dependency/shuffle dependency)和窄依赖（narrow dependency）  

窄依赖就是指父RDD的每个分区只被一个子RDD分区使用，子RDD分区通常只对应常数个父RDD分区，典型的如map，filter，union（常数个父RDD） 
宽依赖就是指父RDD的每个分区都有可能被多个子RDD分区使用，子RDD分区通常对应父RDD所有分区，典型的如groupByKey   

注意上面所说的分区，是RDD->Partition->Record 这个关系里的分区。在Spark中以Partition为单位进行操作。在对stage从后往前拓展时，遇到窄依赖就将其加入stage，遇到宽依赖就断开，重新是一个stage。



## 部署方式
我们需要cluster manager来管理机器，不同的cluster manager就是不同的部署方式
### spark standalone
这里standalone就是通过一种原生的非常plain的方式管理机器，即在对应的节点上手动启动管理进程。比如在master机器上启动./sbin/start-master.sh，在worker机器上启动./sbin/start-worker.sh。这样，机器就加入了spark集群。

### spark on yarn
前面spark standalone的方式比较笨且繁琐，如果有很多机器，有很多类似spark这样的分布式集群应用，那每台机器都要手动运行一下对应的manager process，很麻烦。  
yarn给出了一种统一的管理机器的方式，支持多种分布式集群应用，比如spark，flink这些大数据场景应用。换句话说，是将机器上的spark-worker进程换成了yarn的nodeManager进程，而这种nodeManager进程不仅支持spark，还支持flink等。  
对于spark on yarn，就让yarn帮助我们管理机器，所谓的管理机器呢，我的理解就是处在对应机器上运行的管理进程作为一个代理，是能够帮你分配资源，启动进程等等。此时，driver就是yarn的AppMaster。







# Spark

## 名词
https://spark.apache.org/docs/latest/spark-standalone.html
https://spark.apache.org/docs/latest/cluster-overview.html
glossary: https://spark.apache.org/docs/latest/cluster-overview.html#glossary
- master node
- worker node

- application
  - 
- driver
  - Spark applications run as independent sets of processes on a cluster, coordinated by the SparkContext object in your main program (called the driver program). spark application是用户提交的作业
  - The driver program must listen for and accept incoming connections from its executors throughout its lifetime
- executor
  - processes on worker node that run computations and store data for your application.
  - Each application gets its own executor processes, which stay up for the duration of the whole application and run tasks in multiple threads. 
- task
  - each driver schedules its own tasks
  - tasks from different applications run in different JVMs
- Specifically, to run on a cluster, the SparkContext can connect to several types of cluster managers (either Spark’s own standalone cluster manager, Mesos, YARN or Kubernetes), which allocate resources across applications. Once connected, Spark acquires executors on nodes in the cluster, which are processes that run computations and store data for your application. Next, it sends your application code (defined by JAR or Python files passed to SparkContext) to the executors. Finally, SparkContext sends tasks to the executors to run.

- You can launch a standalone cluster ，或者是running on the Mesos or YARN cluster managers
- The standalone cluster mode currently only supports a simple FIFO scheduler across applications
- 一个application有很多 executors 
- 应用启动模式： For standalone clusters, Spark currently supports two modes. In client mode, the driver is launched in the same process as the client that submits the application. In cluster mode, however, the driver is launched from one of the Worker processes inside the cluster, and the client process exits as soon as it fulfills its responsibility of submitting the application without waiting for the application to finish.