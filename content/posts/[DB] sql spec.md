---
title: "[DB] sql spec"
date: 2021-03-25
tags: ["DB"]
categories: ["DB"]
---

# About sql statement&index spec

> 参考但不限于`Java开发手册（嵩山版）`

## 关于索引

与索引有关的注意事项,基本都集中在一个sql语句它到底是否正确使用了索引,这可以通过explain后的extra列来识别语句执行速度,但是在理论上,我们知道索引是一颗B+树,所以只要了解了B+树的构造,那么自然可以从理论上去识别一个条件查询是否能使用索引

### 联合索引

单键索引没什么好讲的,重点是多键索引

其非叶子节点的搜索键是多个值,比如__(a,b,c) = (4,7,5)__

那么(a<4,\*,\*)会排序到这个索引的左边,如果a == 4,那么再比较b...

所以最终,这个索引的左边会是

__(a<4,\*,\*) , (a=4,b<7,\*),(a=4,b=7,c<5)__

右边会是

__(a>4,\*,\*) , (a=4,b>7,\*) , (a=4,b=7,c>=5)__

#### 使用场景

指定联合索引(a,b,c)

##### 范围查询

如果sql是(语法为EBNF) 

1. where (a < \* | a > \*)
2. where a = * [and (b > * | b < *)]
3. where a = * and b = * [and (c > \* | c < \*)]
4. where a = * order by b

那么显然可以使用b+树的联合索引

> 这就是最左前缀匹配原则

> 并且指定了a后,b,c是天然排序的; 指定a,b同理

##### 失败案例

以下无法使用索引

1. where b = *
2. where b = * and c = *
3. where a > * and b > *
4. where a > * order by b

### 原则

1. 建立联合索引时,区分度最高的在左边(所谓区分度,是指唯一性)
   1. 除非,常用查询是where b = * & a > *,即使a区分度更高,也应该设置索引index_b_a
   2. 这是因为,where b = \*后,对a是天然排序的,若以a为第一个索引,那么查b=\*,就需要对b进行filesort

### 覆盖索引

所谓覆盖索引,就是说对于辅助索引,可以直接查出想要的数据,而不再需要回表查询

### 其他

禁止对索引列进行计算

使用

 `select * from users where adddate<'2007-01-01'`

而不是

`select * from users where YEAR(adddate)<2007`

## Limit

前置条件: k 是辅助索引

`select * from table_name where k = 1 limit  3 offset 100000`

一方面是将会查找出100003条记录,再丢弃掉前100000条记录,这会导致极高的延时

再其次就是会有100003次回表查询(即没找到一个辅助索引对应的pk,就回聚簇索引查找record)

因此,需要使用子查询,防止超多次回表:

`select * from table_name as t1 inner join (select pk from table_name where k =1 limit 3 offset 100000) as t2 on t1.pk = t2.pk `

这其实利用了索引覆盖的特点,由于我们在子查询中是查pk,不需要回表,所以直接放回了100003条pk,然后再统一回表查一次

## Type

要精确存储某个类型时,使用decimal(定点数),而不是浮点数

