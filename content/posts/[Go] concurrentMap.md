---
title: "[Go] concurrentMap"
date: 2021-03-25
tags: ["Go"]
categories: ["Go"]
---

# Built-in map& sync.Map & ConcurrentMap

并发map,是指多线程安全的map数据结构, 我们知道go语言原生的map是不支持并发的, 要想获得一个并发map,

我们有如下的几种方案:

- map with mutex
- sync.Map
  - 读写map分级
- orcaman/concurrent-map
  - 分片

## Map

built-in map本质是动态哈希算法实现,在运行过程中桶会分裂,导致元素的迁移.

- 这也是经典的遍历无序,取出的value不可取地址的原因,以及衍生的value作为结构体时其字段无法赋值的原因

如何处理并发也是一个比较难的问题了,我当时学数据库实现线性哈希的时候也思考了很久这个问题.

但是基于当时的我的知识的思考,其实无异于在想如何开汽车登上月球,没有一定知识积累的思考,真就只是想想而已!

最后,我果断的加上了读写锁 :)



---



这里收录一点关于built-in map的一些冷知识

- 声明和初始化:
  - 空map: 声明+初始化
    - make(map[int]int)
    - map[int]int{}
  - nil map: 声明
    - var a map[int]int
  - 和slice不一样,空map和nil map有着一定的差距
    - 相同: 空map和nil map的读,都会返回default_value,false
    - 不同: nil map的写触发panic,而空map的写正常; nil map可与nil比较为true
  - 相比之下,slice的append操作对于空切片和nil切片都是一致的,除了与nil比较之外

- 任何类型都可以作为key吗?
  - 错,必须是可比较类型;   其中 Slice，Map，Function 是三个内置的唯一的不可比较类型
  - 结构体可比较吗?
    - 同一结构体定义的不同实例: 只要其字段不包含不可比较类型,就可以比较 [ref](https://golang.org/ref/spec#Comparison_operators)
    - 不同结构体定义的不同实例: 显然不行,因为go是强类型语言! 如果它们定义相同,可以尝试先cast
    - 再加上一嘴: 深度比较: reflect.DeepEqual() ,除了判断值,还会判断底层指针指向的值是否相等!
- 删除
  - delete (map\_,key_) , 只会将其删除位置1,而不会释放空间
  - map是一种只增不减的数据结构!
  - 对map的clear,直接创建一个新的map覆盖,原map将会被gc
- 如何有序遍历map

```go
type orderedMap (type T1,t2) struct{
    _map map[T1]T2
    _slice []T1
}
// 假装泛型,这泛型用()小括号是真的让人无语!

func (m *orderedMap(T1,T2))Add(k T1,v T2){
    m._map[k] = v
    m._slice = append(m._slice , v)
    sort.Sort(m)
}

func (m *orderedMap(T1,T2))Iter() func()(T1,T2){
    m = snapshot(m)
    i := -1
    return func(){
        i++
        return m._map[m._slice[i]]
    }
}
```

- 键的优化:     据说, golang为 uint32、uint64、string 作为key时提供了fast access,可以在runtime/map_fast32,... runtime/map_faststr,找到

  - 不过我看了半天代码,发现自己看不懂

  

## Map with mutex

很显然,性能将不再是一个需要多么谈及的话题.mutex将会导致go程阻塞而被调度出运行队列

```go
type concurrentMap(type T1,T2) struct{
    _map map[T1]T2
    rwMutx sync.RWMutex
}

```

## sync.Map

Go1.9 推出了sync.Map

 - 以下场景适合sync.Map:
    - (1) when the entry for a given key is only ever written once but read many times, as in caches that only grow
      	- 这也是concurrent-map的文档里说的,sync.Map只适合append-only的场景(only grow)
    - (2) when multiple goroutines read, write, and overwrite entries for disjoint sets of keys.
      - 根据这个issue:  https://github.com/golang/go/issues/21035   sync: reduce contention between Map operations with new-but-disjoint keys
      - 我想 (2) 应该不再是一个适用场景

其内部实现是用两个built-in map 加 single-mutex 实现

实现:

```go
type Map struct {
	mu Mutex

	// read contains the portion of the map's contents that are safe for
	// concurrent access (with or without mu held).
	//
	// The read field itself is always safe to load, but must only be stored with
	// mu held.
	//
	// Entries stored in read may be updated concurrently without mu, but updating
	// a previously-expunged entry requires that the entry be copied to the dirty
	// map and unexpunged with mu held.
	read atomic.Value // readOnly

	// dirty contains the portion of the map's contents that require mu to be
	// held. To ensure that the dirty map can be promoted to the read map quickly,
	// it also includes all of the non-expunged entries in the read map.
	// 	这里说dirty map can be promoted to the read map,个人感觉会误解为是dirty被promote到了read
    // 实际上也没错,但更准确的是覆盖了,后续的第一次写将会导致遍历read写回dirty.这个遍历更像是promote?
    //
    
	// Expunged entries are not stored in the dirty map. An expunged entry in the
	// clean map must be unexpunged and added to the dirty map before a new value
	// can be stored to it.
	//
	// If the dirty map is nil, the next write to the map will initialize it by
	// making a shallow copy of the clean map, omitting stale entries.
	dirty map[interface{}]*entry

	// misses counts the number of loads since the read map was last updated that
	// needed to lock mu to determine whether the key was present.
	//
	// Once enough misses have occurred to cover the cost of copying the dirty
	// map, the dirty map will be promoted to the read map (in the unamended
	// state) and the next store to the map will make a new dirty copy.
	misses int
}

type readOnly struct {
	m       map[interface{}]*entry
	amended bool // true if the dirty map contains some key not in m.
}

type entry struct {
	p unsafe.Pointer // *interface{}
    // 用指针,是为了方便的 atomic.CompareAndSwapPointer,可以直接修改read.m中本来应该只读的数据
}
// 这里的interface{}, 就是键值对的值,LoadOrStore(k ,v interface{}) 中的v
// 删除: p将指向 unsafe.Pointer(new(interface{}))

func newEntry(i interface{}) *entry {
	return &entry{p: unsafe.Pointer(&i)}
}
```

相信这个图加上上面的注释已经解释的差不多了  [ ref]( https://juejin.cn/post/6844903895227957262)

<img src="http://159.75.75.160/static/sync_map.png" style="zoom:50%;" />

```go
sync的结构为:
type sync.Map{
    mutex
    read{m map[interface{}]*entry , amended }  atomic.Value
    dirty map[interface{}]*entry
    misses
}
```

#### 一文以蔽之

​	**在大多数时刻,dirty都是read.m的超集**,除了dirty刚覆盖read.m后,dirty被置为nil,read.amend置为false,表示read.m即为全部的数据, 在下一次写到来后,将会遍历read.m,将kv存进dirty,并将read.amend置为true,表示dirty是read.m的数据的超集!

​	**什么时候触发dirty对read.m的覆盖?** 当 m.misses >= len(m.dirty)时

> 注意,无效的读Load也会导致miss次数增加! 

### 总结一下sync.map的关键

- 对于本来的map[interface{}] interface{} ,用unsafe.Pointer存储&value, 即unsafe.Pointer是*interface{};
  - 导致可以利用atomic.CompareAndSwapPointer,直接操作readonly map,而无需加锁即可并发
- dirty map大多数时候都是readonly map的超集!除了短暂的dirty覆盖read.m后的nil
- 覆盖后的第一次写dirty,会导致for range read.m, copy键值到dirty

- 适用于读多写少



## ConcurrentMap

>  通过对内部`map`进行分片，降低锁粒度，从而达到最少的锁等待时间(锁冲突)

所谓分片,是指原先的map是一个大map,所有的key计算完的hash都是一个冲突域

但是我现在不再是一个大map,而不是分成多个小map,我先计算key的一个hash,将其映射到小map上,然后对小map操作.

这其实依赖于短时间内多个连续到来的key的hash值不同,那么它们就可以并行,否则就等待锁.

- 在此种情况下,hash函数的选择也至关重要,对于短时间内无序到来的key序列,如何尽可能的计算出短时间内不同的hash值

```go
// A "thread" safe map of type string:Anything.
// To avoid lock bottlenecks this map is dived to several (SHARD_COUNT) map shards.
// shard: 碎片 var SHARD_COUNT = 32
type ConcurrentMap []*ConcurrentMapShared

// A "thread" safe string to anything map.
type ConcurrentMapShared struct {
	items        map[string]interface{}
	sync.RWMutex // Read Write mutex, guards access to internal map.
}

```

#### 写 Store:

很简单,通过 `shard := m.GetShard(key)` 获得该key对应所在的`ConcurrentMapShared`,然后加锁,操作,释放锁;

只要短时间内到来的key计算的hash值不同,那么就不会有`锁竞争`

```go
// Sets the given value under the specified key.
func (m ConcurrentMap) Set(key string, value interface{}) {
	// Get map shard.
	shard := m.GetShard(key)
	shard.Lock()
	shard.items[key] = value
	shard.Unlock()
}
```

hash函数(Fowler–Noll–Vo hash function)  [ref](https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function)

```go
func (m ConcurrentMap) GetShard(key string) *ConcurrentMapShared {
	return m[uint(fnv32(key))%uint(SHARD_COUNT)]
}

// Fowler–Noll–Vo hash function:
func fnv32(key string) uint32 {
	hash := uint32(2166136261) 
	const prime32 = uint32(16777619)
	for i := 0; i < len(key); i++ {
		hash *= prime32
		hash ^= uint32(key[i])
	}
	return hash
}
```

这个并发map最核心的思想已经讲完了,简单,却实用! 单个map也许做不了并发,但两个map(`一读一写,写是读超集`)搭配一个锁就可以做还行的并发,多个平行的map加 `map级别的锁`就能做很不错的并发

除了并发的核心,这个库的其他代码其实也值得学习!

#### 比如并发中的扇入模式

- 利用chan,每个shard开启一个go程,并发返回所有的Key:

> 如果是同步的算法,那么时间复杂度是O(n^2),遍历了两次. 但使用了go程进行并发加速
>
> 第一次计算有多少个key,即count,是有必要的,正是这个数值的确定,导致我们可以安心的创建count个缓冲的chan,并关闭通道
>
> 对于无缓冲通道,适合只有一个go程生成数据,常见于lazy evaluate

```go
// Keys returns all keys as []string
func (m ConcurrentMap) Keys() []string {
	count := m.Count()
	ch := make(chan string, count)
	go func() {
		wg := sync.WaitGroup{}
		wg.Add(SHARD_COUNT)
		for _, shard := range m {
			go func(shard *ConcurrentMapShared) {
				shard.RLock()
				for key := range shard.items {
					ch <- key
				}
				shard.RUnlock()
				wg.Done()
			}(shard)
		}
		wg.Wait()
		close(ch)
	}()
	keys := make([]string, 0, count)
	for k := range ch {
		keys = append(keys, k)
	}
	return keys
}

```

#### 有缓冲优于无缓冲

```go
// Iter returns an iterator which could be used in a for range loop.
//
// Deprecated: using IterBuffered() will get a better performence
func (m ConcurrentMap) Iter() <-chan Tuple {
	chans := snapshot(m)
	ch := make(chan Tuple)
	go fanIn(chans, ch)
	return ch
}

// IterBuffered returns a buffered iterator which could be used in a for range loop.
func (m ConcurrentMap) IterBuffered() <-chan Tuple {
	chans := snapshot(m)
	total := 0
	for _, c := range chans {
		total += cap(c)
	}
	ch := make(chan Tuple, total)
	go fanIn(chans, ch)
	return ch
}
```

个人认为,对于有缓冲的通道,有一个特别大的优点就是,发送完数据就可以直接关闭了;

而如果无缓冲,就会一直阻塞,依赖于读的速度

```go
shard.RLock()
chans[index] = make(chan Tuple, len(shard.items))
wg.Done()
for key, val := range shard.items {
    chans[index] <- Tuple{key, val}
}
shard.RUnlock()
close(chans[index])
```



---

用一个简单的map分片解决了并发问题,而且肉眼可以看出性能不会太差,虽然占空间, 但仍然可以称之为优雅!