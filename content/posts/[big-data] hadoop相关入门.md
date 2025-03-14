---
title: "[BigData] 大数据入门"
date: 2022-04-10
categories: ["BigData"]
tags: ["BigData"]
---

# 大数据
未来工作或多或少要接触大数据，学习下。

# glossary
- hadoop， 可以认为大数据平台就是hadoop平台/hadoop集群的代名词
- hadoop集群作为基础设施，主要包括存储和调度。存储是hdfs（hadoop distributed file system），调度是yarn（yet another resource negotiater），在计算方面，一般是和用户强相关的，执行的是用户传入的Job，在计算框架上，一般有MapReduce/Spark/Flink等。使用这些分布式计算框架实现的作业，当被yarn调度从而运行时，一般称之为“XX On Yarn”，比如"Spark On yarn"


## Hdfs
- hdfs是一个流式的分布式的文件存储系统
- 存的是文件，但不是以文件为单位分布式副本存储；而是将文件切分成多个小块block（一个block 128MB），每个block将按照一定的副本策略存在多个机器上。
- hdfs的架构主要分为NameNode和DataNode，DataNode存储文件块数据，NameNode存储元数据
  - 元数据包括1.目录树信息 2.文件到块的映射 3.块到DataNode的映射
- hdfs还包括secondaryNameNode，不过这个进程不是很重要，他的工作主要合并日志，NameNode对于写文件操作，一般不是直接进行随机内存访问的直接修改磁盘上的持久化的文件目录数和映射关系（称作fsimage），而是将写操作以日志追加的方式append到一个叫做edit.log的文件中，类似于各种AOF，WAL，secondaryNameNode的工作就是合并fsimage和edit.log（按道理来说，这个合并应该直接让NameNode分出一个线程来合并就完事了，但是这里独立了一个进程，优劣性可以再讨论）
- hdfs是流式的，这意味着文件只能追加，不能修改。一次写入，多次读。
- 在写操作时，先写到本地临时文件，当文件大小达到一个块后，开始以4KB为一个packet发送给第一个DataNode，第一个DataNode会接受并转发给第二个DataNode（递归形式），当文件全部写完后，文件才可见。

## Yarn
- Yarn是资源管理调度器，所谓的资源是硬件资源，包括内存，CPU，磁盘，网络等，以容器的形式交付给应用
- 我感觉就是k8s+docker的感觉，提供统一的nodeManager和容器资源交付。
- 架构上是资源管理器（分为资源调度器和应用程序管理器）+节点管理器
  - 资源调度器根据需要的资源声明交付容器
  - 应用程序管理器管理应用的提交，与资源调度器协商资源等
  - 节点管理器，顾名思义，节点代理，实际上的工作者，分配容器资源，启动工作进程等。
- 每个任务的提交需要三个东西
  - 应用的Master程序（ApplicationMaster），比如MapReduceApplicationMaster，类似于k8s中CRD Operator的感觉，比如spark中的driver就是这种appMaster程序（也就是spark的main程序，包含sparkcontext）
  - 应用的Master程序的启动程序，估计是启动脚本一类的。
  - 用户程序，比如用户自己编写的MapReduce程序

> 我比较好奇容器是怎么交付的，可以深究一下


## MapReduce
- 没啥，一个计算框架呗，将输入输出的过程分为：
  - Input
  - 无状态Map，比如map，flatmap， filter，foreach
  - 有状态Reduce，比如reduceby，sortby，group， fold
  - Output
- 用户只需要在特定的阶段编写自己的代码即可
- 本质上就是提供对单个元素操作，以及对一群元素操作的api，可以看看spark.rdd暴露的[api](https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.RDD.reduceByKey.html)


## HBase
- 宽列NoSQL
- 逻辑上表可以看成是稀疏行的数据库，但物理上表按列族存储
- Table -> Region -> Store 
  - 一张表在行方向上会划分为多个Region（一开始只有一个Region，行多了就划分多个Region），不同的Region在不同的RegionServer上存放，一般一个RS可以放10-1000个Region，每个Region的元数据包括1.表名 2.首行 3.末行。由于有首末行，很容易知道一个将要插入的行应该插入哪个Region，联系哪个RegionServer
  - Region是分布式存储的最小单元，所以一行数据会放在一个节点（RegionServer）上，但在节点机器上，不同列族的存储是分开的。
  - Region由多个Store构成，一个Store就是一个列族，包含MemTable和SSTable。
  - 存储上的结构有待研究，一般是二进制自己封装个block，一个block包含rowkey，ts，columnFamily，column，value等，然后各个block按rowkey排序，相同的rowkey的不同column会排到一起。



## Hive
- Hive是一个工具，将HiveQL转成MapReduce任务（也可以是spark任务）,一个简单的例子是HBase不支持SQL，所以可以使用HiveQL操作HBase
- Hive建立在hdfs或相关生态之上（比如hbase）
- Hive在普通的查询语句之前，要先建表
- 关于建表，数据存储，可以看看[这个](https://blog.csdn.net/xxydzyr/article/details/100915053)。
- 简单来说就是，hive建立的表是一种虚拟的表，相当于只是一种元数据schema。表里的数据是存在hdfs上的，当你建完表之后，就会在hive对应的hdfs路径里自动创建一个该表的文件夹，你需要自己把你的数据文件拷贝进去。然后就可以通过hql查询了。后续应该是直接把数据存到hive对应的hdfs里。
- hive还支持一种external表，可以指定对应的数据存储的hdfs路径，而不需要将数据放到hive对应的路径里面。
- 一般来说，文件里的一行就是一个record，在行里面，需要指定列分隔符来划分列。

### Hive表Hbase表映射

通过"hbase.columns.mapping"设置映射关系，按position一对一，:key可以省略，cf0:indexId代表映射到hbase的cf0列族的indexId列（没有写对应的hive的列明，因为按位置顺序一对一映射，也就是hive中的indexId）  
- 如果是外部表，数据就是存在hbase
- 如果有设置"hbase.mapred.output.outputtable"，往hive插入数据也会插入hbase，否则就是单向的hbase到hive的映射

如果想将hive的people表的内容输出到hbase的hbase_people表，可以创建一个hive的hive_people表作为中继，如下面的代码，然后执行插入`insert overwrite table hive_people  select * from people where age = 17;`
```
CREATE EXTERNAL TABLE hbase_table_2(key int, indexId string, muMac string) 
STORED BY 'org.apache.hadoop.hive.hbase.HBaseStorageHandler' 
WITH SERDEPROPERTIES ("hbase.columns.mapping" = ":key,cf0:indexId,cf0:muMac") 
TBLPROPERTIES("hbase.table.name" = "default:index1");


create table hive_people
(
id int,
name string,
age string,
sex string, 
edu string, 
country string, 
telPhone string,  
email string
)
stored by 'org.apache.hadoop.hive.hbase.HBaseStorageHandler'
with serdeproperties ("hbase.columns.mapping" = "
:key,
basic_info:name,
basic_info:age,
basic_info:sex,
basic_info:edu,
other_info:country,
other_info:telPhone,
other_info:email
")
tblproperties("hbase.table.name" = "default:hbase_people","hbase.mapred.output.outputtable" = "default:hbase_people");
```

可以考虑hive的可视化连接工具dbeaver

## Spark
- 并行计算框架
- 支持流式(spark streaming)或批式(spark core)
- spark streaming 会将流处理成一个个窗口，所以其实底层还是批式的spark core
- 部署方式有spark standalone， spark on yarn
- 参看大数据系列下一篇专门介绍spark的文章