---
title: "[data-structure] skip-list"
date: 2021-03-25
tags: ["data-structure"]
categories: ["data-structure"]
---

# skipList

跳表具有平均的O(logn)的时间复杂度,但最坏情况仍是O(n)

跳表是二叉搜索树,AVL,RBTree的替代品

这里我们不介绍如何从头开始编写skipList,但仍然介绍其中可能存在的一些关键点



## 数据结构

### C

如果是用c语言,我们可以这样实现一个skipList的底层数据结构

摘自: [begeekmyfriend/skiplist](https://github.com/begeekmyfriend/skiplist/blob/master/skiplist.h)

>  其中用到了1.柔性数组 2.从成员还原出结构体首地址 等一些trick
>
> 用1.柔性数组,是为了保证link与skipnode是内存连续性,以便于使用2来还原出首地址,这样,st_link就不必去记录*node了,少了一个开销
>
> 柔性数组也是动态分配的,用多少分配多少,避免多余浪费

```c
struct sk_link {
        struct sk_link *prev, *next;
};
struct skiplist {
        int level;
        int count;
        struct sk_link head[MAX_LEVEL];
};
struct skipnode {
        int key;
        int value;
        struct sk_link link[0];
};
```

在st_link中,我们记录了prev,这是为了方便插入.否则如果只记录next,那么在插入前的search时,就要记录一张表,便于插入时的指针赋值



### Go

在go中,一般实现成:

摘自: https://github.com/sean-public/fast-skiplist

```go
type elementNode struct {
	next []*Element
}

type Element struct {
	elementNode
	key   float64
	value interface{}
}
```

这里,len(next)就表示这个node的高度,next[i]就是第i层指向的下一个节点,不同层可能会指向到相同的节点,所以有可能next[0] == next[1]



### 思考

为什么不适用上层节点也是node结构呢? 我在[youtube的某些视频](https://www.youtube.com/watch?v=783qX31AN08)上看到上层节点也是node,从代码上看,很优美对称,但是会有数据的冗余.

而且当使用额外的link结构后(c的写法),也完美的继承了这种对称,即逐层的遍历节点

```c
struct skipnode {
        int key;
        void* value;
        struct skipnode *right;
    	struct skipnode *down;
};
```



## 插入

在学习时,你可能学的是一层一层构建skiplist,先遍历第一层,每个node抛硬币,看自己是否能构建上层

但在实践中,这没有必要,我们直接用一个random函数决定一个节点有几层即可

> 注意,不是简单的抛到几就是几,仍然是逐层增长的,因为概率是乘法,详见后文的概率表

```c
static struct skipnode *
skiplist_insert(struct skiplist *list, int key, int value)
{
        int level = random_level();
        if (level > list->level) {
                list->level = level;
        }
        struct skipnode *node = skipnode_new(level, key, value);
    	// do search and insert
}
```

### 搜索并插入

首先搜索

从最高层开始逐步顺着指针遍历,找到end.key>newNode.key,prev.key<newNode.key

然后插入,将newNode插入到prev和node之间

__list_add(a,b,c) 函数将a插入在b,c之间,注意a,b,c只是单个st_link

并向下一层移动(即pos--,end--),此时for循环由于条件直接满足而被跳过,直接执行插入

```c
int i = list->level - 1;
for (; i >= 0; i--) {
    pos = pos->next;
    for (; pos != end; pos = pos->next) {
        struct skipnode *nd = list_entry(pos, struct skipnode, link[i]);
        if (nd->key >= key) {
            end = &nd->link[i];
            break;
        }
    }
    pos = end->prev;
    if (i < level) {
        __list_add(&node->link[i], pos, end);
    }
    pos--;
    end--;
}

static inline void
__list_add(struct sk_link *link, struct sk_link *prev, struct sk_link *next)
{
        link->next = next;
        link->prev = prev;
        next->prev = link;
        prev->next = link;
}
```

## Go中的插入

为什么要单独谈论c和go的实现呢? 因为c的语言特性决定了它可以写的很炫,但是go就只能很plain的实现

首先创建新节点

```go
element = &Element{
    elementNode: elementNode{
        next: make([]*Element, list.randLevel()),
    },
    key:   key,
    value: value,
}
```

然后找到key该插入的位置在各层的前一个node(注意,这个

prevs的各个元素可能属于不同的node),因为每个node的高都不同

```go
prevs := list.getPrevElementNodes(key)
```

执行插入,遍历当前element/node的高度,替换指针

```go
for i := range element.next {
    element.next[i] = prevs[i].next[i]
    prevs[i].next[i] = element
}
```

### 搜索

还记得我在前面说的插入前的搜索要维护一张表吗,就是这里的`list.prevNodesCache`

```go
func (list *SkipList) getPrevElementNodes(key float64) []*elementNode {
	var prev *elementNode = &list.elementNode
	var next *Element

	prevs := list.prevNodesCache

	for i := list.maxLevel - 1; i >= 0; i-- {
		next = prev.next[i]

		for next != nil && key > next.key {
			prev = &next.elementNode
			next = next.next[i]
		}

		prevs[i] = prev // 这里prevs[i]存了整个prev,其实只需要存prev[i]即可,不过反之都是指针,开销到是一样的. 是这样吗?详见后面描述的caching and search fingers
	}

	return prevs
}
```



### 关于重复键值

这其实取决于你的上层数据结构的逻辑,如果你是要实现一个set,那显然不能有重复键值,遇到重复的,就直接覆盖

## 超参数

根据这个[repo](https://github.com/sean-public/fast-skiplist),指出了合适的超参数选择

1. 抛硬币为正面的概率P为1/e,即向上增长的概率为1/e(典型的p的取值为0.25->0.5)

> The default *P* values for skip lists in the wild range from 0.25 to 0.5. In this implementation, the default is *1/e*, which is optimal for a general-purpose skip list. To find the derivation of this number, see [Analysis of an optimized search algorithm for skip lists](http://www.sciencedirect.com/science/article/pii/030439759400296U) Kirschenhofer et al (1995).

2. 随机数生成器PRNG 

我们不能使用全局的随机数生成器,因为这样的化,多个跳表之间就会造成冲突,有锁的竞争

因此,每个跳表一个rand.Source

```go
randSource:     rand.New(rand.NewSource(time.Now().UnixNano())),
```

## 概率表

一个典型的层数将如下计算

```go
static int random_level(void)
{
        int level = 1;
        const double p = 0.25;
        while ((random() & 0xffff) < 0xffff * p) {
                level++;
        }
        return level > MAX_LEVEL ? MAX_LEVEL : level;

```

很明显,我们可以预先记录好一个概率表,然后只计算一次rand,这意味着,我们将这一次rand视为多次rand的乘积,而概率表也是概率的乘积,因此直接比较

```go
func probabilityTable(probability float64, MaxLevel int) (table []float64) {
	for i := 1; i <= MaxLevel; i++ {
		prob := math.Pow(probability, float64(i-1))
		table = append(table, prob)
	}
	return table
}
func (list *SkipList) randLevel() (level int) {
	// Our random number source only has Int63(), so we have to produce a float64 from it
	// Reference: https://golang.org/src/math/rand/rand.go#L150
	r := float64(list.randSource.Int63()) / (1 << 63)

	level = 1
	for level < list.maxLevel && r < list.probTable[level] {
		level++
	}
	return
}
```



## 缓存,caching and search fingers

当我们把整个节点缓存下来,有利于后面的搜索,而不仅仅是缓存那一层,见https://github.com/sean-public/fast-skiplist#caching-and-search-fingers

## Conclusion

个人认为go中的实现可能更好,因为它避免了去逐层的访问,而是统一的去访问一个node,再去访问他的next数组,找到对应层的下一个node