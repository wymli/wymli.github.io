---
title: "recommend system"
date: 2021-04-13
categories: ["dataMining"]
tas: ["dataMining"]
---

# 推荐系统

utility matrix效用矩阵,横轴是用户,纵轴是商品,矩阵元素是打分

推荐系统的三个核心步骤:

- 收集效用矩阵中的打分
- 从已知的打分中预测未知的打分
- 评估预测性能

## Gathering Ratings

我们可以显式让用户打分或付钱让它们打分,也可以从它们的行为推测分数,比如它们经常观看,或购买

但是utility matrix是稀疏的,大多数人对大多数item都是没有打分的,并且新用户和新item都是没有值的

我们主要介绍三种方法:

- 基于内容的
- 协同的
- 基于潜在因子的

## 基于内容的推荐

主要思想: 仅考虑用户自己,我们向用户推荐这样的商品,这些商品和用户之前的高打分商品类似

比如电影,我们已知用户的一些高打分电影,于是向用户推荐同一个导演,演员等等的电影

### Item profile

因此,我们需要为每个item建立一个profile,profile是一些特征的集合,比如电影就是导演,演员,剧本作者等等,网页就是一些关键字集合

对于文本网页来说,如何选择重要的关键字特征呢?

我们使用 TF-IDF score,当一个关键字在该网页出现的越多,在其他网页出现的越少,我们就认为该关键字的TF-IDF指标高,更能代表该doc

TF-IDF score:
$$
w_{ij} = TF_{ij} * IDF_i
$$
其中:
$$
TF_{ij} = \frac{f_{ij}}{max_kf_{kj}} , IDF_i = log\frac{N}{n_i}
$$
f_ij 表示term/feature i 在 doc/item j中的频率,n_i表示有多少个doc提到了term i,N是总的doc数

### User profile

它已打分的一些item的加权平均数据

## 推荐

给定user profile x和item profile i,我们通过余弦相似度来判断是否相似

### pros & cons

优点:

- 不需要其他user的信息
- 能够按用户的口味推荐
- 能够推荐新的或不流行的item
- 可解释性

缺点:

- 寻找合适的feature去构建item profile是较难的
- 对于新用户,没有user profile,无法推荐
- 过于专一化,绝不推荐user的content profile之外的item,用户也许想有不同的兴趣



## 协同过滤

我们首先找到N个其他user,这些user对item的打分与user x的打分是类似的,我们基于这N个用户的打分来预测x的打分,所以叫协同

## 寻找相似的user

### jaccard 相似度

如果我们不考虑具体的打分多少,而只考虑有没有打分,然后可以对集合计算jaccard相似度

### cos 相似度

我们将未打分的item视作0,于是一个user对应的item就是一个向量,计算余弦即可

### pearson 互相关系数

皮尔森互相关系数,具体公式见ppt,这是统计里面相关性检验常用的方法

## 协同过滤

假设utility矩阵是user x item的

## user-user 协同过滤

即只考虑一列,通过一列上的其他相似user的值来预测自己,N代表与那些对i打过分的user中的与x最相似的k个user,s_xy代表x与y的相似度
$$
r_{xi} = \frac{\sum_{y∈N}s_{xy}*r_{yi}}{\sum_{y∈N}s_{xy}}
$$


## item-item 协同过滤

即只考虑一行,通过一行上的其他相似item的值来预测自己
$$
r_{xi} = \frac{\sum_{j∈N}s_{ij}*r_{xi}}{\sum_{j∈N}s_{ij}}
$$

## pros & cons

优点:

- 不需要选择feature,对所有类型的item都适用

缺点

- 冷启动
- first rater,对于未被打分过的新item,不能推荐
- popularity bias,一般会倾向于推荐热门的item,而不是对味的item