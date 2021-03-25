---
title: "[Go] goroutine pool"
date: 2021-03-25
tags: ["Go"]
categories: ["Go"]
---

# Goroutine Pool

> 代码来自:gobwas/ws-example

在go中,由于goroutine是完全的用户态线程,所以创建新线程的开销很小,在这种情况下,复用goroutine形成goroutine池的优化效果很有限

但是,池不仅减少了创建开销,还能有效的限制对象个数

因此,假如我们的服务期望有最大的goroutine个数限制,将需要使用goroutine pool

## 设计

一个goroutine pool需要什么呢?

需要: 当前运行的gorotine数,最大goroutine数,任务队列,条件变量/信号量(用于线程阻塞等待任务)

但是在go中,chan是天然的一个阻塞队列,任务队列本身就完成了阻塞唤醒的功能

对于curr_n_thread和max_n_thread,本来应该用两个int去存,但是在go中,也可以用chan struct{},因为有缓冲的通道天然有上限,并且增加减少都是并发安全的

> 虽然用`sem  chan struct{}`表示goroutine数目的限制很炫,但是确实不如int去存有用,毕竟int能反映当前运行的goroutine数目,而`sem  chan struct{}`只能限制最大数

```go
type Pool struct {
	sem  chan struct{}
	work chan func()
}
```

### NewPool

创建一个pool

> size: max_n_thread
>
> queue: 等待队列上限(最大等待任务数)
>
> spawn: 立即运行多少工作线程

```go
func NewPool(size, queue, spawn int) *Pool {
	if spawn <= 0 && queue > 0 {
		panic("dead queue configuration detected")
	}
	if spawn > size {
		panic("spawn > workers")
	}
	p := &Pool{
		sem:  make(chan struct{}, size),
		work: make(chan func(), queue),
	}
	for i := 0; i < spawn; i++ {
		p.sem <- struct{}{}
		go p.worker(func() {})
	}

	return p
}
```

### 分配任务

只需要简单的往通道里丢任务就可以了

注意,这里的实现是有问题的,原作者可能是想实现:优先想p.work发送任务,如何P.work满了还没有被消费,就新开一个工作线程

但是go的select是没有顺序的,所以我们必须拆分一下

```go
func (p *Pool) Schedule(task func()) {
	p.schedule(task, nil)
}

func (p *Pool) schedule(task func(), timeout <-chan time.Time) error {
	select {
	case <-timeout:
		return ErrScheduleTimeout
	case p.work <- task:
		return nil
	case p.sem <- struct{}{}:
		go p.worker(task)
		return nil
	}
}
```

=>

```go
func (p *Pool) schedule(task func(), timeout <-chan time.Time) error {
    select{
    case p.work <- task:
		return nil
    default:
    }
    
    select {
	case <-timeout:
		return ErrScheduleTimeout
	case p.work <- task:
		return nil
	case p.sem <- struct{}{}:
		go p.worker(task)
		return nil
	}
}
```

或:

```go
select {
	case <-timeout:
		return ErrScheduleTimeout
	case p.work <- task:
		return nil
	case p.sem <- struct{}{}:
        select{
            case p.work <- task:
            	<- p.sem
            	return nil
            default:
        }
		go p.worker(task)
		return nil
}
```

### 工作线程等待分发任务

由于chan的自阻塞性,极易实现,当然这个没有实现线程的退出,如果想实现,可以使用一个退出chan,然后每个线程去竞争done,就像竞争任务一样

```go
func (p *Pool) worker(task func()) {
	defer func() { <-p.sem }()

	task()

	for task := range p.work {
		task()
	}
}
```

加了退出通道的工作线程

```go
func (p *Pool) worker(task func()) {
	defer func() { <-p.sem }()

	task()

	for task := range p.work {
		task()
        select{
        case <- p.done:
            return
        default:
        }
	}
}

func (p *Pool) ReduceOne(){
    p.done <- struct{}{}
    p.work <- func(){} // 发送一个空任务,防止工作线程阻塞在p.work而接收不到p.done
}
```

当然,更好的写法是直接同等地位的判断p.work和p.done:

```go
func (p *Pool) worker(task func()) {
	defer func() { <-p.sem }()

	task()

    for {
        select{
            case task := <- p.work:
            	task()
            case <- p.done
            	return
        }
	}
}
```

## Ants库

github上看到了一个5.2k star的协程库,首先不管技术架构和代码风格,看到readme的几张大图,就感动的哭了,这就是所谓的一分钟上手!

1h后,我只想说挺捞的.

readme有很多错误或不足:

- 作者似乎区分不清throughput和one-way latency;
- 配图也比较老旧了,和代码对不上;
- go test , 某些协程发生了panic
- 性能测试是基于工作是sleep的,这相当于又将开销放到了go自己的阻塞调度上

我自己基于如下的工作函数重新测了下:

```go
func demoFunc() {
	begin := time.Now()
	i := 0
	for {
		i++
		end := time.Now()
		if end.UnixNano()-begin.UnixNano() > int64(time.Millisecond)*10 {
			return
		}
	}
}
```

```go
goos: windows
goarch: amd64
pkg: a/ants
cpu: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
BenchmarkPlainPool
BenchmarkPlainPool-8                   1        13103489000 ns/op        6123848 B/op
  54292 allocs/op
BenchmarkGoroutines
BenchmarkGoroutines-8                  1        13296742800 ns/op        4290672 B/op
  10006 allocs/op
BenchmarkAntsPool
BenchmarkAntsPool-8                    1        13276752000 ns/op        2631920 B/op
  41997 allocs/op
PASS
ok      a/ants  39.795s
```

这里的plainPool指的就是我们上面自己实现的pool

可以看到,整个的吞吐率是差不多的,测试完成时间都是13s(所以加起来是39s),但是ants确实降低了1倍的内存消耗

至于单向提交延迟,我个人感觉意义不太大.协程池的主要优点应该在内存上,避免了无节制的新建内存.

但是话又说回来,如果只是避免内存,那只需要加个计数器来限制就好了



于是给ants提了个issue: https://github.com/panjf2000/ants/issues/144



## Conclusion

协程池是有必要的,它所保证的__内存消耗与协程调度的上限__,增强了服务器对DOS攻击的耐受性.

除此之外,在go中的优势似乎没有太多,不过,即使只有一点,也够了.

