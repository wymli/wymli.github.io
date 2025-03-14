---
title: "[BigData] spark"
date: 2022-04-15
categories: ["BigData"]
tags: ["BigData"]
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

### transformation 算子和action 算子的区别
Transformation是lazy的，用于定义新的RDD；而Action启动计算操作，提交一个Job，并向用户程序（driver，yarn的appMaster）返回值或向外部存储写数据


## 部署方式
我们需要cluster manager来管理机器，不同的cluster manager就是不同的部署方式
### spark standalone
这里standalone就是通过一种原生的非常plain的方式管理机器，即在对应的节点上手动启动管理进程。比如在master机器上启动./sbin/start-master.sh，在worker机器上启动./sbin/start-worker.sh。这样，机器就加入了spark集群。

### spark on yarn
前面spark standalone的方式比较笨且繁琐，如果有很多机器，有很多类似spark这样的分布式集群应用，那每台机器都要手动运行一下对应的manager process，很麻烦。  
yarn给出了一种统一的管理机器的方式，支持多种分布式集群应用，比如spark，flink这些大数据场景应用。换句话说，是将机器上的spark-worker进程换成了yarn的nodeManager进程，而这种nodeManager进程不仅支持spark，还支持flink等。  
对于spark on yarn，就让yarn帮助我们管理机器，所谓的管理机器呢，我的理解就是处在对应机器上运行的管理进程作为一个代理，是能够帮你分配资源，启动进程等等。此时，driver就是yarn的AppMaster。

#### 详细流程
yarn集群模式为例，部署模式也是cluster；参考 [here](https://cangchen.blog.csdn.net/article/details/120278516)

> spark deploy部署部分的代码在[此处](https://github.com/apache/spark/tree/master/core/src/main/scala/org/apache/spark/deploy)

1. spark-submit.sh [脚本](https://github.com/apache/spark/tree/master/sbin)开始提交，参数master指定yarn，java代码指定jar包--jar和主类名--class（main函数在的类，这和java运行机制相关），其他语言如python/r，只要指定文件即可
2. spark-submit.sh 脚本调用scala org.apache.spark.deploy.SparkSubmit类，下称之为SparkSubmit进程
3. 根据调用参数--deploy=cluster,--master=yarn，现在调用org.apache.spark.deploy.yarn.YarnClusterApplication，
4. SparkSubmit进程创建一个YarnClient，提交Application给yarn集群的ResourceManager，提交成功后返回appid，如果spark.submit.deployMode=cluster&&spark.yarn.submit.waitAppCompletion=true， SparkSubmit进程会定期输出appId日志直到任务结束(monitorApplication(appId))，否则会输出一次日志然后退出。
     1. 这就是deploy=cluster模式，如果是deploy=client模式，就不需要提交。
5. YarnClient通过提交Application的过程
```scala
launcherBackend.connect()
yarnClient.init(hadoopConf)
yarnClient.start()

logInfo("Requesting a new application from cluster with %d NodeManagers"
  .format(yarnClient.getYarnClusterMetrics.getNumNodeManagers))

// Get a new application from our RM
val newApp = yarnClient.createApplication()
val newAppResponse = newApp.getNewApplicationResponse()
appId = newAppResponse.getApplicationId()

// The app staging dir based on the STAGING_DIR configuration if configured
// otherwise based on the users home directory.
val appStagingBaseDir = sparkConf.get(STAGING_DIR)
  .map { new Path(_, UserGroupInformation.getCurrentUser.getShortUserName) }
  .getOrElse(FileSystem.get(hadoopConf).getHomeDirectory())
stagingDirPath = new Path(appStagingBaseDir, getAppStagingDir(appId))

new CallerContext("CLIENT", sparkConf.get(APP_CALLER_CONTEXT),
  Option(appId.toString)).setCurrentContext()

// Verify whether the cluster has enough resources for our AM
verifyClusterResources(newAppResponse)

// Set up the appropriate contexts to launch our AM
val containerContext = createContainerLaunchContext(newAppResponse)
val appContext = createApplicationSubmissionContext(newApp, containerContext)

// Finally, submit and monitor the application
logInfo(s"Submitting application $appId to ResourceManager")
yarnClient.submitApplication(appContext)
launcherBackend.setAppId(appId.toString)
reportLauncherState(SparkAppHandle.State.SUBMITTED)
```
6. 在提交应用时，yarn客户端首先调用yarn.createApplication()获取newAppResponse（其中包括appID），随后构建容器和应用上下文appContext，最终提交应用yarn.submitApplication(appContext)，yarn客户端通过传入appContext真正提交应用。appContext包括容器启动上下文（`containerContext = createContainerLaunchContext(newAppResponse)`）和应用提交上下文（`appContext = createApplicationSubmissionContext(newApp,containerContext)`）
7. 我们来看是如何构建容器启动上下文的，createContainerLaunchContext(newAppResponse)：
```scala
if (isClusterMode) {
  Utils.classForName("org.apache.spark.deploy.yarn.ApplicationMaster").getName
} else {
  Utils.classForName("org.apache.spark.deploy.yarn.ExecutorLauncher").getName
}
val commands = prefixEnv ++
      Seq(Environment.JAVA_HOME.$$() + "/bin/java", "-server") ++
      javaOpts ++ amArgs ++
      Seq(
        "1>", ApplicationConstants.LOG_DIR_EXPANSION_VAR + "/stdout",
        "2>", ApplicationConstants.LOG_DIR_EXPANSION_VAR + "/stderr")
```
对于deploy=cluster的appMaster的容器启动命令简单来看就是`bin/java -server org.apache.spark.deploy.yarn.ApplicationMaster --class … --jar ...`
8. 应用通过yarnClient提交后，yarn集群某一个NodeManager收到ResourceManager的命令，启动ApplicationMaster进程。ApplicationMaster会启动driver。
```scala
if (isClusterMode) {
  runDriver()
} else {
  runExecutorLauncher()
}
```
1. 下面是runDriver()的流程，先另启动一个线程通过反射执行命令行中-–class指定的类（org.apache.spark.examples.SparkPi）中的main函数。同时在主线程会向ResourceManager作为AppMaster注册自己。
```scala
// 1. startUserApplication 启动用户应用main代码
val mainMethod = userClassLoader.loadClass(args.userClass)
      .getMethod("main", classOf[Array[String]])
val userThread = new Thread {
      override def run(): Unit = {
          mainMethod.invoke(null, userArgs.toArray)
      }
}
userThread.setContextClassLoader(userClassLoader)
userThread.setName("Driver")
userThread.start()

// 2. 向rm注册am
registerAM(host, port, userConf, sc.ui.map(_.webUrl), appAttemptId)
// 3. 申请exector的资源
createAllocator(driverRef, userConf, rpcEnv, appAttemptId, distCacheConf)
  // createAllocator()函数内部
  // 3.1 创建申请客户端
  allocator = client.createAllocator(
      yarnConf,
      _sparkConf,
      appAttemptId,
      driverUrl,
      driverRef,
      securityMgr,
      localResources)
  // 3.2 申请资源并沟通对应的nm，执行exector容器
  allocator.allocateResources()
    // allocateResources()函数内部
    // 3.2.1 获取containers
    val allocateResponse = amClient.allocate(progressIndicator)
    val allocatedContainers = allocateResponse.getAllocatedContainers()
    // 3.2.1 筛选contaienrs，根据主机host，机架rack等信息筛选出要使用的containers
    matchContainerToRequest(allocatedContainer, ANY_HOST, containersToUse,
        remainingAfterOffRackMatches)
    // 3.2.3 启动容器
    runAllocatedContainers(containersToUse)
      // runAllocatedContainers()内部
      // 3.2.3.1 调用ExecutorRunnable
      for (container <- containersToUse) {
        new ExecutorRunnable(
                  Some(container),
                  conf,
                  sparkConf,
                  driverUrl,
                  executorId,
                  executorHostname,
                  executorMemory,
                  executorCores,
                  appAttemptId.getApplicationId.toString,
                  securityMgr,
                  localResources,
                  ResourceProfile.DEFAULT_RESOURCE_PROFILE_ID // use until fully supported
                ).run()
      }
      // 3.2.3.2 执行ExecutorRunnable.run()方法,沟通nodeManager
      def run(): Unit = {
        logDebug("Starting Executor Container")
        nmClient = NMClient.createNMClient()
        nmClient.init(conf)
        nmClient.start()
        startContainer()
      }
      def startContainer(){
        val commands = prepareCommand()
        ctx.setCommands(commands.asJava)

        nmClient.startContainer(container.get, ctx)
      }
      def prepareCommand(){
        val commands = prefixEnv ++
          Seq(Environment.JAVA_HOME.$$() + "/bin/java", "-server") ++
          javaOpts ++
          Seq("org.apache.spark.executor.YarnCoarseGrainedExecutorBackend",
            "--driver-url", masterAddress,
            "--executor-id", executorId,
            "--hostname", hostname,
            "--cores", executorCores.toString,
            "--app-id", appId,
            "--resourceProfileId", resourceProfileId.toString) ++
          userClassPath ++
          Seq(
            s"1>${ApplicationConstants.LOG_DIR_EXPANSION_VAR}/stdout",
            s"2>${ApplicationConstants.LOG_DIR_EXPANSION_VAR}/stderr")
      }

```

> 这一套流程走下来，我觉得应该看看yarnclient~，即怎么与yarn交互。


## 提交任务
https://spark.apache.org/docs/2.2.0/submitting-applications.html
通过名为spark-submit.sh的脚本，指定master的地址即可提交到spark standalone或yarn。



## 其他
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