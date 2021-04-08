# 聚类

聚类是一种无监督的方法,我们仅仅通过向量的特征即可将不同的向量按相邻的距离聚在一起

对于输入的数值元组的不同的视角,我们可以定义不同的距离

- 将元组视为向量
  - 计算cos距离来求解相似度,即余弦值,可有余弦定理计算得出
- 将元组视为集合
  - 计算jaccard距离,即A∩B/A∪B
- 将元组视为欧氏空间中的坐标点
  - 计算欧式距离

## 层次聚类

方法是不断的将小聚类合并(合并两个最近的聚类),形成大的聚类,从单个点作为一个聚类开始

也可以是top down的方法,不断将大聚类split,但一般采用bottom up方法

- 聚类的代表
  - centroid : average of its points(这要求欧式空间(欧式距离),此时直线最短,所以直接求平均,便是聚类的中心点)
    - centroid 可能不是一个实际存在的点
  - clustroid: point closest to other points
    - clustroid一定是一个实际存在的点
- 聚类内closest的定义(clustroid选举)
  - 某个点关于其他所有点的最大距离最小,则这个点是clustroid
  - 某个点关于其他所有点的平均距离最小
  - 某个点关于其他所有点的距离平方和最小
- 聚类间nearness定义(聚类合并选择)
  - 将clustroid视作centroid,计算两个cluster的centroid/clustroid之间的距离
    - 注意如果没有定义欧式距离就没有centroid,但一定会有距离的定义,只是不是直线最短
  - 分别从两个聚类选择两个点,得到的最小的距离即使聚类之间的距离
  - 凝聚度(计算合并后的聚类的凝聚度)
    - 直径: 聚类内的点之间的最大距离
    - 平均距离: 聚类内所有点之间的平均距离
    - 密度: 使用直径或平均距离除以点数,密度越小越好(相同直径下,点越多,密度越小,聚类越密集)
- 看网上其他博客,基本都采用这样的距离定义来计算聚类间的nearness:
  - 聚类间两点距离的最小值
  - 聚类间两点距离的最大值
  - 聚类间两点距离的平均值

## k-means 算法

> 这里的k指的是k个聚类

首先会给每个聚类随机初始化为1个点,也就是我们要随机选取k个点,每个点作为一个聚类.

但显然,如果随机选,可能选到两个很近的点,因此针对初始化的不同,提出了k-means++算法,二者仅仅在初始化时不同,后续跌打是一样的

- 初始化
  - 随机
  - k-means++
    - 随机遍历点,但是否将它们加入初始点集合取决于它与已加入初始点集合内的点的最短距离的平方
    - 因此,以这种方法选出来的k个初始点将会尽可能的远
  - 于是,每个cluster都有了一个centroid
- 聚类
  - 遍历所有点,将其加入离他最近的centroid所属的cluster(你可以认为也遍历了初始点,反正肯定离自己最近,当迭代一次后,一般centroid都不再是实际存在的点)
  - 遍历完后,更新cluster的centroid位置
  - 重新遍历所有点,加入离他最近的centroid所属的cluster
    - 此时,点对cluster的所属关系可能变更
  - 重复上述过程
- 收敛
  - 当点对cluster的所属关系不再变更,并且centroid稳定时,认为收敛
- k的选择
  - 我们计算聚类内的点到centroid的平均距离作为k的好坏,平均距离越小,k越好
  - 实践证明,k越大,平均距离越小,当大到一定程度后,平均距离几乎不变,此时即为最佳的k

## BFR 算法

> 算法名字是三个发明人的首字母

BFR算法是k-means算法的变种,用于解决大规模数据集问题(这些数据集一般驻留在磁盘上)

首先我们假设聚类内的点是关于centroid呈正太分布的,不同的维度的标准差不同,这意味着一个聚类将会很像一个关于轴对齐的椭圆(一个轴就是一个维度)

> ? 我们的目标是找到cluster的centroid,然后就可以按照k-means的算法,对所有点计算得到离他最近的centroid,并归入那个cluster(这称为point assignment)

算法流程:

1. 初始化k个cluster的centroid
2. 加载一些point到内存
3. 对这些点进行point assignment,前提是最小距离小于一定的阈值,如果这些点离最近的centroid的距离大于所设置的阈值,则将这些点视为outlier离群点
4. 将离群点独立为一个cluster,于是现存k+1个cluster
5. 对k+1个cluster中的两个cluster执行merge,生成k个cluster
6. 重复2-5



我们将维护三类点集

- Discard set(DS): 能够被分配给某个cluster的点(我们可以加载它,计算统计信息,然后丢弃这个实例,有点充分统计量的感觉)
- Compression set(CS): 一些足够近的点的集合,但这些点离最近的centroid足够远,所以独立成为一个cluster
- Retained set(RS): 孤立的等待被分配给CS压缩集的点

每个discard set将会维护2d+1个值,d是向量的维度

- 1: 点数
- d: sum向量,sum_i代表set内的所有点的第i个分量的和
- d: sumsq向量,sumsq_i代表sum_i的平方

有了这三个数值,我们可以很方便的计算ds的centroid和方差(centroid就是每个维度的平均值,sum/N , 方差就是(sumsq/N) - (sum/N)^2),我们不需要知道到底哪些点属于ds,我们唯一要维护的就是这三个统计量

> 注意,cluster是轴对齐的,这样的好处是sumsq是一个d维向量,而不是一个dxd的二维协方差矩阵

将点加载到内存,如果发现这些点离某个centroid足够近,就将这些点分配给那个cluster,并添加到ds

这样,一次加载进内存的点将还会剩下一些点没有进入任何集合,这些点由于离现存的centroid们比较远而无法进入discard set,现在我们对这些在内存中的点运用任何in-memory的聚类方法分类即可,我们要分出两类,一类是compression set,一类是retained set

比如我们直接对剩下的点随机初始化几个centroid(或使用层次聚类),然后遍历所有点,如果离这些centroid足够近,就加入这些cluster对应的compression set,否则便是离群点,加入retained set

下一步,我们首先处理ds,之前加入ds的点,在这一步用于更新ds的统计量(N,sum,sumsq)(实际上这一步完全可以放在加入ds时就直接更新统计量)

然后,考虑合并compressed set,如果这是最后一轮,那么合并compressed set和ratained set到最近的cluster中

### 距离

使用mahalanobis distance(马氏距离),点x到centroid点c的距离定义为:
$$
d(x,c) = \sqrt{\sum_{i=1}^d(\frac{x_i-c_i}{\sigma_i})^2}
$$
即对每个维度进行标准化,然后求平方和的根号

根据3sigma原则, 当x_i = c_i + sigma_i或c_i - sigma时,dist = sqrt(d)

此时,有68%的概率,使得dist<sqrt(d),如果x服从正态分布

一般的,我们认为一个点x属于某个cluster,如果dist<2sqrt(d)

 

### 合并

何时合并cs中的集合呢? 如果合并后的方差小于某个阈值,则合并两个compressed set



## CURE

...