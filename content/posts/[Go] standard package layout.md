---
title: "[Go] standard package layout"
date: 2021-03-25
tags: ["Go"]
categories: ["Go"]
---

# Standard Package Layout

标准包布局   -Ben Johnson https://www.gobeyond.dev/standard-package-layout/

Vendoring和Generics,它们在go社区似乎都是big issue,但还有一个很少提及的issue,就是应用的包布局(application package layout)

每个我所参与的go应用都似乎对一个问题有不同的答案,我应该如何组织我的代码?有些应用将所有东西堆到一个包里面,但是还有一些应用会选择按type或module来分组. 如果没有一个好的策略能在整个团队中贯彻使用,你会发现代码会分散在应用的各个包中(译者注:即强耦合).我们需要一个更好的go应用设计的标准

我建议这样的一个更好的方法. 通过遵循一些简单的规则我们可以解耦我们的代码,使得它更加容易测试,并且为我们的项目带来一致性的结构.在我们深入探讨之前,先看看现在最常见的一些人们组织包的方法

## 有缺陷的方法

似乎存在一些常用的方法来组织go包,但它们都有这自己各自的缺陷

### 方法#1: 单包(译者注:类比单内核/宏内核)

将你的代码扔在一个包里确实对于一些小应用来说可以运行的很好.它避免了循环依赖的可能,因为在你的应用里面,没有任何依赖(译者注:即引用别的包)

我曾看见过这样的方式能对至多10k行源码的应用起效.但超过这个大小后,就会使浏览代码和隔离代码变得非常困难

### 方法#2: Rails风格布局

另一种方法是按功能类型来对代码分包.比如,你所有的handlers放在一个package,所有的controllers放在一个package,所有的models放在一个package.我在过去的Rails开发者中经常看见这种布局

但是这个方法仍然存在两个问题.首先,你的命名是atrocious的.你最终得到类似controller.UserController这样的类型名称,这意味着你在类型名中重复了包名.我倾向于对命名有一定的质量要求(stickler).当你陷入杂草般的代码中时,我相信名字是最好的文档.名字也被用作是对代码质量的代理(译者注:即命名是代码质量的外显/一部分)(a proxy for quality)-因为它是某个人阅读代码时最先注意到的东西.

但是,最大的问题是环形依赖. 不同的功能类型也许需要互相引用彼此. 这样的按功能类型分包的布局只会在你的依赖都是单向时才有效,但是大部分情况你的应用都不会那么简单.

### 方法#3: 按模块分包

> 译者注: 类似于按照类来分包?

这个方法与Rails风格布局相似,但此时我们按模块进行分包来组织我们的代码,而不是功能.比如,你有一个users包和一个accounts包.

在这个方法中,我们将会发现和Rails风格中同样的问题.再一次,我们最终得到了类似users.User这样糟糕的命名.我们也同样面临环形依赖的问题,如果accounts.Controller需要和users.Controller进行交互,反之亦然.

## 一个更好的方法

我使用的应用在我们项目中的分包策略包括四个简单的宗旨:

1. 根包用于领域类型(译者注:根包即net/http中的net,其含有与http子包并列的代码文件)
2. 按依赖对子包分组
3. 使用共享的mock子包(mock模拟,译者注:用于测试)
4. Main包将捆绑所有依赖(译者注:Main包是可执行包,将会引用所有需要的依赖,此外的子包不可以平行引用子包)

这些规则帮助隔离我们的包和在整个应用中定义一个清晰的领域语言.让我们看看每一个规则是如何在实践中生效的

### 1.根包用于领域类型

你的应用有一个逻辑的,高层次的语言来描述数据和进程的交互. 这就是你的领域(domain).如果你有一个电商应用,你的领域将包含诸如顾客,账户,对信用卡收费,处理库存等.如果你是Facebook,那么你的领域将是用户,爱好,关系网等. 领域所包含的东西就是一些不依赖于你底层技术的东西

我将我们的领域类型放在根包中.这个包只包含简单的数据类型比如User结构体,用于持有用户数据或UserService接口用于存取用户数据

代码可能长这样:

```go
package myapp

type User struct {
	ID      int
	Name    string
	Address Address
}

type UserService interface {
	User(id int) (*User, error)
	Users() ([]*User, error)
	CreateUser(u *User) error
	DeleteUser(id int) error
}
```

这会使得你的根包非常小. 你也可以包含执行操作的类型,但前提是它们仅依赖于其他领域类型.比如,你可以有一个用于周期性轮询UserService的类型.但是它不可以访问外部的服务(service)或保存数据到数据库.这是一个实现细节.(译者注:即不能引入更多的包(外部包/子包),只能用现有的类型)

根包不应该依赖其他任何在你应用中的包(译者注:不应该依赖子包)

### 2.按依赖来分包

> (译者注:比如http依赖在一个包,数据库依赖在一个包)

如果你的根包不允许有外部的依赖,那么我们必须将这些依赖放置在子包中(译者注:根包不应该有任何import).在这个关于包布局的方法中,子包作为一个你的领域和你的实现之间的适配器存在(译者注:核心观点,子包作为领域与实现的适配器,而实现将使用外部依赖,这中间通过接口适配,便于mock)

比如,你的UserService也许由Postgresql支持.你可以在你的应用中引入一个名为postgres的子包用于提供postgres.UserService实现(译者注:app.postgres.UserService结构体实现app.UserService接口)

```go
package postgres

import (
	"database/sql"

	"github.com/benbjohnson/myapp"
	_ "github.com/lib/pq"
)

// UserService represents a PostgreSQL implementation of myapp.UserService.
type UserService struct {
	DB *sql.DB
}

// User returns a user for a given id.
func (s *UserService) User(id int) (*myapp.User, error) {
	var u myapp.User
	row := db.QueryRow(`SELECT id, name FROM users WHERE id = $1`, id)
	if row.Scan(&u.ID, &u.Name); err != nil {
		return nil, err
	}
	return &u, nil
}

// implement remaining myapp.UserService interface...
```

这段代码隔离了我们的Posgresql依赖,简化了测试(译者注:这称为依赖注入)和提供了简单的方法用于未来可能的迁移数据库.它可以被用作一种可插拔架构(pluggable architecture),如果你决定支持其他的数据库实现比如BoltDB.

它也给了你一种对实现分层的方法.也许你想要持有一个在内存中的,LRU算法的cache在PostgreSQL之前.那么你只需要添加一个实现了UserService的UserCache,它可以包装(wrap)你的PostgreSQL实现(译者注:装饰模式)

```go
package myapp

// UserCache wraps a UserService to provide an in-memory cache.
type UserCache struct {
        cache   map[int]*User
        service UserService
}

// NewUserCache returns a new read-through cache for service.
func NewUserCache(service UserService) *UserCache {
        return &UserCache{
                cache: make(map[int]*User),
                service: service,
        }
}

// User returns a user for a given id.
// Returns the cached instance if available.
func (c *UserCache) User(id int) (*User, error) {
	// Check the local cache first.
        if u := c.cache[id]]; u != nil {
                return u, nil
        }

	// Otherwise fetch from the underlying service.
        u, err := c.service.User(id)
        if err != nil {
        	return nil, err
        } else if u != nil {
        	c.cache[id] = u
        }
        return u, err
}
```

我们在标准库中也看到了这种方法.io.Reader是一个领域类型,用于读字节,它的实现按依赖进行分组(分包)----tar.Reader,gzip.Reader,multipart.Reader. 它们也可以被分层叠起来,我们经常可以看到os.File被bufio.Reader包装,再被gzip.Reader包装,再被tar.Reader包装.

#### 依赖之间的依赖

你的依赖们并没有隔离.你也许会存储User数据到PostgreSQL中,但你的金融交易数据存放在第三方服务中,比如Strip. 在这个例子中我们使用一个逻辑领域类型来包装Strip依赖---让我们叫他TrasactionService.

通过添加TransactionService到UserService,我们解耦了这两个依赖:(译者注:这里是myapp.posgres.UserService,而不是myapp.UserService,   myapp.posgres.UserService实现了myapp.UserService)

```go
type UserService struct {
	DB                 *sql.DB
	TransactionService myapp.TransactionService
}
```

现在这些依赖仅通过公共领域语言来进行通信. 这意味这我们可以将PosgreSQL切换成MySql,或者切换Strip为另一个支付处理器,而不影响其他依赖.

#### 不要局限于第三方依赖

> (译者注:对于标准库也要隔离)

这听起来可能很奇怪，但是我也使用这种相同的方法来隔离我的标准库依赖. 例如,net/http包只是另一个依赖. 我们也可以通过在应用程序中包含http子包来隔离它.(译者注:所谓隔离一个包,是指只在特定的包引入一个包,而不是在应用中到处引用)

具有与其包装的依赖相同名称的包似乎很奇怪,但是,我是故意的. 除非您允许在应用程序的其他部分中使用net/http，否则您的应用程序中没有程序包名称冲突. 复制名称的好处是它要求你将所有HTTP代码(译者注:与http通信相关的代码)隔离到http包中.

```go
package http

import (
        "net/http"
        
        "github.com/benbjohnson/myapp"
)

type Handler struct {
        UserService myapp.UserService
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
        // handle request
}
```

现在，http.Handler充当您的域和HTTP协议之间的适配器

### 3. 使用共享的mock子包

因为我们的依赖通过领域接口与其他依赖隔离，所以我们可以使用这些连接点来注入模拟实现.(译者注:依赖注入)

有许多模拟库（例如GoMock）可以为你生成模拟，但我个人更喜欢自己编写mock. 因为我发现许多模拟工具过于复杂.

我使用的模拟非常简单. 例如, UserService的模拟如下所示:

```go
package mock

import "github.com/benbjohnson/myapp"

// UserService represents a mock implementation of myapp.UserService.
type UserService struct {
        UserFn      func(id int) (*myapp.User, error)
        UserInvoked bool

        UsersFn     func() ([]*myapp.User, error)
        UsersInvoked bool

        // additional function implementations...
}

// User invokes the mock implementation and marks the function as invoked.
func (s *UserService) User(id int) (*myapp.User, error) {
        s.UserInvoked = true
        return s.UserFn(id)
}

// additional functions: Users(), CreateUser(), DeleteUser()
```

>  译者注:此处的mock只涉及了是否调用,对于更verbose的mock,还可能涉及调用顺序等

这个mock让我们可以注入函数到任何使用myapp.UserService接口的地方,我们可以借此来验证参数,返回期望数据,或者注入失败

比如我们想测试我们之前定义的http.Handler:

```go
package http_test

import (
	"testing"
	"net/http"
	"net/http/httptest"

	"github.com/benbjohnson/myapp/mock"
)

func TestHandler(t *testing.T) {
	// Inject our mock into our handler.
	var us mock.UserService
	var h Handler
	h.UserService = &us

	// Mock our User() call.
	us.UserFn = func(id int) (*myapp.User, error) {
		if id != 100 {
			t.Fatalf("unexpected id: %d", id)
		}
		return &myapp.User{ID: 100, Name: "susy"}, nil
	}

	// Invoke the handler.
	w := httptest.NewRecorder()
	r, _ := http.NewRequest("GET", "/users/100", nil)
	h.ServeHTTP(w, r)
	
	// Validate mock.
	if !us.UserInvoked {
		t.Fatal("expected User() to be invoked")
	}
}
```

mock让我们完全隔离单元测试到仅仅的http协议的处理上(译者注:如果没有mock,则单元测试将包含UserService的创建和http协议的处理,UserService的创建可能依赖很多东西)

### 4.Main包将捆绑所有依赖

现在所有这些依赖都被隔离地漂浮在那里了, 您可能想知道它们是如何组合在一起的. 这就是main包的工作.

#### Main包的布局

一个应用也许会产生出很多二进制文件,所以我们将使用Go的传统,将main包作为cmd包的一个子目录.比如,我们的项目也许有一个myapp的服务器二进制文件,但也有一个myappctl的客户端二进制文件用于通过终端管理服务器.我们列出这个main包的布局:

```go
myapp/
    cmd/
        myapp/
            main.go
        myappctl/
            main.go
```

> 译者注: 一定要在app/cmd下再创建一个子目录,否则go build/go install出来默认是目录名,即cmd,且go install没办法rename

#### 编译时注入依赖

术语"依赖注入"从字面上描述的并不好.它使人想到了冗长的Spring XML文件. 但是,这个术语真正表示的是我们将要向对象传递依赖(译者注:作为NewXXX函数的参数传入),而不是要求这个对象自己建立或找到依赖.

main包就是我们选择哪个依赖被注入哪个对象的地方. 因为main包简单地将一小块一小块的依赖连接在一起(译者注:原文:wires up the pieces, 可见google/wire命名由来),它往往是比较小且琐碎的代码:

```go
package main

import (
	"log"
	"os"
	
	"github.com/benbjohnson/myapp"
	"github.com/benbjohnson/myapp/postgres"
	"github.com/benbjohnson/myapp/http"
)

func main() {
	// Connect to database.
	db, err := postgres.Open(os.Getenv("DB"))
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Create services.
	us := &postgres.UserService{DB: db}

	// Attach to HTTP handler.
	var h http.Handler
	h.UserService = us
	
	// start http server...
}
```

同样重要的是要注意到,你的main包也是一个适配器(adapter). 它连接终端到你的领域.

## 结论

应用设计是一个很难的问题. 存在太多需要做出的设计决策,并且如果没有一系列可靠的原则去指引你,问题将会被弄得更糟. 我们研究了当前Go应用程序设计的几种方法,并且发现了它们的许多缺陷.

我相信从依赖关系的桀骜都着手进行设计将会使得代码组织的更简单,也更容易究因. 首先我们设计领域语言.然后我们隔离依赖.再接着我们引入mock来隔离测试. 最后,我们将所有内容捆绑在一起放在main包

在下一个你设计的应用程序中考虑这些原则. 如果你有任何问题或想要讨论设计, contact me at [@benbjohnson](https://twitter.com/benbjohnson) on Twitter or find me as **benbjohnson** on the [Gopher slack](https://gophersinvite.herokuapp.com/).

---

译者: @https://github.com/liwm29 

概括: 按依赖分包,各子包将实现根包定义的interface,且它们之间不可以互相import. 根包定义领域类型,如果依赖外部服务,则定义interface.最终在cmd/app/main.go中完成依赖注入