---
title: "[other] everyDay"
date: 2021-03-25
tags: ["other"]
categories: ["other"]
---

# 12.1
1. 重新学习了gin的一部分用法,比如参数获取,文件上传,静态文件目录之类的,我感觉任何东西还是要先学会用,再去看源码学习
2. 看了一篇微服务的概述,看起来微服务的兴起就像操作系统的历史一样,由宏内核到微内核,将函数作为服务提供调用,微服务则是将不同的功能组件独立成独立的网络服务,分布在不同的主机;为了降低延迟,使用rpc而不是http,使用protobuf(?存疑)而不是json/xml,因为解析速度不够;带宽方面,随着计算机性能的提升,一般没问题,记得chenshuo在muduo教程里面测过通过本机tcp端口做ipc,带宽也非常可观.目的还是降低单次调用的延时
3. 看了下go语言的sync.map源码,实现上类似于双缓冲区,涉及到写缓冲区的操作一律加锁,默认一个读一个写,加快速度,读不到了再从写的那个缓冲区读;miss次数一定后,就更新缓冲区(用写缓冲区直接覆盖读缓冲区,写缓冲区置为0,后续第一次写入写缓冲区时,会先将读缓冲区的数据拷贝过来,为什么这样设计,可能只是语言机制语法上的妥协吧);
   1. 关于写,如果在读缓冲区读到了(注意读到了还要考虑是不是被删除了),就用cas写(换指针),否则上锁,去写缓冲区;
   2. 关于读,读缓冲区没读到,并且两个缓冲区数据不一致(定义两个缓冲区数据一致指的是写缓冲区为0,即刚将写缓冲区覆盖读缓冲区),就上锁,去写缓冲区读;
   3. 删除: 将指向value的指针置为nil,但本身还存在map中,延迟删除
   4. 还有一个特点是,获取锁后,不要立即访问写缓冲区,而是再访问一次读缓冲区,因为你不知道有没有其他线程触发更新,使得写缓存区清空了
4. 把win10升级到了专业版,可以用remote desktop了

# 12.2
1. remote desktop 的延迟还是挺高的,仅仅能用
2. 继续说sync.map,其中还是有很多东西可以说到说到的
   1. 乐观锁与悲观锁
      1. 数据库中的概念
      2. cas(compare&swap),或者是test&set,这些原子指令认为是无锁的,lock-free
         1. 但这并不意味着它们代价低,事实上cas作为一个写指令,一定会在总线上发出BusX(后续会写的读信号)信号,以失效多核cpu的其他核的cache,保证cache一致性,然后才读到数据,compare失败或成功
         2. 因此一个典型的优化是read and cas,先读,因为处理器读导致BusRead不会使cache失效,这其实就是要减少cas的强制占用总线,后续也可能会有多个核cas,但没关系,最多是核数而不是线程数
      3. 乐观锁,倾向于数据少写
         1. 先不加锁访问(读),直到更新的时候再用cas更新,可以通过比较version字段(或要修改的值的最新状态与之前的快照)来比较,然后update
            1. 如果是全局的version字段,就不会有ABA问题
            2. 如果失败,就回滚,重新search
         2. 所以其实乐观锁不算是一种锁
      4. 悲观锁,倾向于数据多写
         1. 强制加锁,访问
   2. 复制的效率
      1. 可以看到读缓冲区miss后将要访问写缓冲区时,写缓冲区要先copy读缓冲区,再写新的key&value
      2. 这是说明了复制的效率一定高于加锁PV的效率?


# 12.13
- 一下子就10天没写了,自己还是太懒了,但是这十天还是接触了很多东西的
- authentication and authorization, 认证与鉴权
  - 在go里面,认证可以用jwt,鉴权可以用casbin,一般鉴权是rbac,role-based-access-control,基于角色的访问控制,鉴权就是访问控制
  - 这其实就类似于Kerberos,有认证服务器和票据服务器,二者分开
- go语言并发,daisy chain之类的东西,输入channel,开goroutine对数据filter,输出channel
- reactor,proactor,两种事件处理模式,event-driven
  - reactor是主线程只负责监听事件发生(epoll_wait),然后分发任务给任务线程,读写数据都在工作线程中完成,accept()也在worker中完成
  - proactor是异步io的,将io操作交给主线程/内核完成,我们知道异步本质就是注册一个回调函数,当io结束后执行回调函数
  - 不够,感觉没太大用,因为目前还接触不到应用的场景
- reactiveX,流式处理数据,一种异步io风格
  - 但是和回调又有点不同,它是源源不断接收流式的数据,然后对数据像流水线一样处理. 当然本质也就是注册回调函数,但可以避免过多callback时候的混乱代码,主要是语法上更简介吧
- 看了beego的session模块的代码,感觉写的确实收益颇多
  - 因为可以有不同的存储场景,所以用interface在中间层抽象,应用层(应用者,user)和底层(提供者,provider)都面向interface编程,底层存储提供者可以是memory,file,redis,db等等,这需要编写对应的驱动(虽然我不知道这叫不叫驱动,但是确实在功能上给我一种驱动的感觉,一般会称之为adapter吧,适配器)
  - 它的并发链表的实现也不错,一方面用链表存储数据,另一方面为了解决链表线性访问慢的问题,用map存储链表的node,快速查找sessionId对应的node
    - 为什么要用container/list呢,而不直接用sync.map存储session,这是因为,我们还要计算其超时时间!
    - 我们不可能遍历所有的node去计算其超时,所以必须要按时间排序
    - 在这里,list就充当了这个角色,新创建的session被放到list的前面,快超时的session自然在最后面,在gc的时候只需要不断测试最后一个node就好了
      - 另外这种定时事件,好像都是用小顶堆做的,这里用链表其实也不错
      - container/list提供了极其方便的api,比如:PushFront,MoveToFront,Remove
    - 何时GC,处理超时session:
      - 在sessionInit时,就goroutine一个线程定时gc,可以用递归的形式,比较优雅.当然放在一个for{}无穷循环里面也可
      - func(m *manager)gc(){m.provider.gc(); time.AfterFunc(time.Duration , m.gc)}
    - 在哪里告诉程序,这个provider实现了?
      - 直接在init()中register,维护一个全局的map即可,实现了就在这个文件的init函数中往map里面写就可以了,极其容易拓展,低耦合
    - 注意session只需要管理一个sessionId和对应的value就行了,value可以是任何值的集合,可以设成map[string]interface{},虽然其实go也支持map[interface{}]interface{}
      - session不需要管理对应的url路径什么的,那是cookie的事,我们在response的时候要set-cookie,对应的cookie值在那里设置,value设置成对应的sessionId即可
  - MVC架构
    - model-view-controller
      - model就是一个个定义的结构体/类对象,其实主要还是用来访问数据库的,其他的名字:DAO,data-access-object,数据访问对象,也就是orm,object-relation-model
      - view,就是前端视图了,可能是一些模板之类的
      - controller就是后端处理逻辑,hanler,middlerware,log,session,router之类的
  - 综合看下来,beego不完全是一个web框架,它还集成了client,定时任务task之类的模块,我感觉非常值得学习,而且谢大的书go web编程也是开源的,顶礼膜拜好吧
- VUE
   - 在看奇淼在b站录的vue视频,感觉这个人教学方面是很不错的,视频看下来不会让我感觉无聊,讲的也比较有激情,知识点归纳的也不错
   - 在我入门gin的情况下去听了下他的gin入门课,感觉还是很不错的,也有收获
   - 之前接触的那些开源项目的目录结构都很迷,初学者完全看不懂为什么这么摆,他的gin-vue-admin的项目目录结构就比较清爽,一目了然
 - vue-router
   - 前端页面路由,用来构建单页面应用
   - 表现上就是一个页面内的标签页/导航
   - 典型的,前端路由可以用在登陆界面上,就不用登陆界面单独写一个后端路由/html了
# 12.14
- 这一周打算: 
  - 学会vue/element ui的布局layout,一个典型的后台管理系统就是单页面的,在固定的框类切换不同的内容,所以建立好总体的布局尤为重要
  - 了解http2,简单看了下,感觉都在说什么连接复用,头部压缩之类的,但是http1.0/1.1不是也已经支持keep-alive了吗?这两个长连接的区别?
  - 了解redis?redis就是一个键值对的数据库,经常用作缓存
  - 看到了vue-element-admin,是个不错的项目,而且有教程,基本和奇淼的gin-vue-admin是一个东西,不过这也是因为后台管理系统确实就是那一套.但是对我来说,依然还是有很多学习的地方的
- todo
  - 组件上的v-model
  - 子组件的this.emit('input',)
  - 根组件
    - 就是new Vue()
  - 组件一定要被<template>包含?
  - 直接获取组件对象:
    - 根组件: $root
    - 父组件:$parent 只读
    - 子组件:$children 只读,无序
      - 若想改变子组件的内容,只能直接改变子组件所引用的数组的内容,子组件由v-for生成
  - <slot>插槽
    - 用来指示外部传给组件的innerHTML的显示位置
    - 比如<my-button>"this is innerHTML"</my-button>
  - vue的入口文件:
    - 入口可以是 main.js、index.js、App.vue 或 app.vue 中的一个
    - 哪个定义了new Vue()实例,哪个就是入口
  - vue实例内置数据/方法,前加$,比如var vm = new Vue({el:"",data:{}}),vm.\$el,vm.\$mount()
    - 只有在初始创建时在data字典里面的数据才是响应式的,后面添加的都必须手动触发更新
- 关于layout
  - 一般来说,后台管理系统是单页面的,简洁好用,没必要设计成跳来跳去的跳转
  - 一般的,用侧边栏来导航,el-main块用来显示内容,如何实现点击不同的按钮,main块切换到不同的页面内容呢?
    - 这个其实element-ui直接实现了,叫标签页
    - 但是如果想更灵活一点,可以自己设计,是通过vue-route实现的
    - main块放<router-view>即可
- 标签页是容易实现的,可以用它来练习组件,设计插槽,父子组件通信这些
  - 本质就是一个tab组件,子组件是tab-pane代表各个标签,tab只是控制tab-pane的显示而已,而显示可以用v-if,很简单
- 一个标准的vue前端代码结构是: ./component , ./App.vue , ./main.js
  - 在main.js中引入全局组件,App.vue是入口文件
- 组件通信: 父传子:props down ; 子传父:events up : this.$emit()
- 关于vue的组件,强推这个课程:https://www.bilibili.com/video/BV1nx411X7oA


# 12.16
- 前后端分离,不仅仅是独立开发,也是独立部署,这意味着后端仅仅是提供api的路由!而由前端自己提供页面的路由,这就是意味着前端有自己的路由
# 12.18
- 前后端分离,前端一般是单页面的,通过内置前端路由实现多页面,但只有一个vue实例,请求后端api服务器可能需要设置跨域
  SPA,单页面应用的路由有两种模式:hash和history,这两种方法都可以改变uri而不触发浏览器的刷新(向服务器请求)
  - 如果是history模式,又没有前后端分开部署(即服务端渲染),指浏览器直接向后端服务器请求html,这时候手动刷新页面就会触发对后端的请求,但因为是前端路由,在后端中不存在,所以需要后端特别配置,后端当收到不存在的路由时,直接返回index.html,index.html将自动根据浏览器栏的path跳转到特定的前端路由,此时要注意设置前端路由的404,用'*'匹配即可
- 了解了vue的路由,以及子路由
- todo:
  - import , export default,export const这些是什么
- 未来目标: 重构一下sysu_jwxt_v2,前后端分离,后端仅作为api服务器