---
title: "[container] 6.容器基础之runc源码"
date: 2025-03-14
categories : ["container"]
tags : ["container", "oci", "runc"]
---

git clone https://github.com/opencontainers/runc.git, 我们简单阅读下，代码不多

# 入口
入口没啥好说的，先找main.go文件，可以看到runc这个库用了 github.com/urfave/cli 这个命令行库和 github.com/sirupsen/logrus 这个日志库，能在这种比较重要的工具里面使用，说明这两个库是很不错的。

# create
create的实际作用是由runc拉起一个 runc（通常称为parentProcess，也就是 runc create ... 这个进程） 拉起一个子runc进程（通常称为childProcess, 或更精确的，initProcess），子runc进程的执行命令为 `runc init`, 执行后会进行所有ns/rootfs的初始化操作，并阻塞在打开exec.fifo命名管道上，等待start指令，收到指令之后会立即执行system.Exec原地将自己替换成用户主进程。  
这里有无start其实都不太重要，create之后容器环境就创建好了，后续无论是start还是exec都行，一个是执行config.json里的主进程，一个是执行exec命令行里的进程。   
 

## notify.sock 创建
如果指定了环境变量 NOTIFY_SOCKET， 会创建notify.sock  
默认创建在 ${root}/${container_name}/notify/notify.sock, root是/run/runc 或者 /run/user/1000/runc
```
notifySocket := newNotifySocket(context, os.Getenv("NOTIFY_SOCKET"), id)
if notifySocket != nil {
    notifySocket.setupSpec(spec) // 在 config.json 中添加 notify.socket 的mount和env
}

// ...
// 创建容器 ...
// ...

if notifySocket != nil {
    if err := notifySocket.setupSocketDirectory(); err != nil { // 创建目录和权限 os.Mkdir(path.Dir(s.socketPath), 0o755)
        return -1, err
    }
    if action == CT_ACT_RUN { // 如果是在运行容器，就生成socket文件
        if err := notifySocket.bindSocket(); err != nil {
            return -1, err
        }
    }
}
```

notifySocket 的主要逻辑其实就是监听 notify.socket, 转发到用户自定义的 socket addr, 应该是用来实现一些事件驱动的   

```
func (n *notifySocket) run(pid1 int) error {
	if n.socket == nil {
		return nil
	}
	notifySocketHostAddr := net.UnixAddr{Name: n.host, Net: "unixgram"}
	client, err := net.DialUnix("unixgram", nil, &notifySocketHostAddr)
	if err != nil {
		return err
	}

	ticker := time.NewTicker(time.Millisecond * 100)
	defer ticker.Stop()

	fileChan := make(chan []byte)
	go func() {
		for {
			buf := make([]byte, 4096)
			r, err := n.socket.Read(buf)
			if err != nil {
				return
			}
			got := buf[0:r]
			// systemd-ready sends a single datagram with the state string as payload,
			// so we don't need to worry about partial messages.
			for _, line := range bytes.Split(got, []byte{'\n'}) {
				if bytes.HasPrefix(got, []byte("READY=")) {
					fileChan <- line
					return
				}
			}

		}
	}()

	for {
		select {
		case <-ticker.C:
			_, err := os.Stat(filepath.Join("/proc", strconv.Itoa(pid1)))
			if err != nil {
				return nil
			}
		case b := <-fileChan:
			return notifyHost(client, b, pid1)
		}
	}
}
```

## systemd on-demand socket
这里学到一个新知识，systemd on-demand socket，大致意思时，配置一个systemd的socket文件，监听某个端口，再配置一个systemd的service文件，关联某个socket文件，随后，当请求打到socket文件关联的端口时，会启动service文件，做到按需启动的功能。
```
// Support on-demand socket activation by passing file descriptors into the container init process.
listenFDs := []*os.File{}
if os.Getenv("LISTEN_FDS") != "" {
    listenFDs = activation.Files(false)
}

// ...
if len(r.listenFDs) > 0 {
    process.Env = append(process.Env, "LISTEN_FDS="+strconv.Itoa(len(r.listenFDs)), "LISTEN_PID=1")
    process.ExtraFiles = append(process.ExtraFiles, r.listenFDs...) // 应该是为了容器内的进程可以读到LISTEN_FD
}
```
回头专门开一章跑个demo试试，有点faas的意思

## create container
```
func createContainer(context *cli.Context, id string, spec *specs.Spec) (*libcontainer.Container, error) {
	rootlessCg, err := shouldUseRootlessCgroupManager(context) // 内容暂时看不懂，反正就是准备rootless cgroup配置
	if err != nil {
		return nil, err
	}
	config, err := specconv.CreateLibcontainerConfig(&specconv.CreateOpts{ // 这一步是将runc 的config转成 libcontainer的config
		CgroupName:       id,
		UseSystemdCgroup: context.GlobalBool("systemd-cgroup"),
		NoPivotRoot:      context.Bool("no-pivot"),
		NoNewKeyring:     context.Bool("no-new-keyring"),
		Spec:             spec,
		RootlessEUID:     os.Geteuid() != 0,
		RootlessCgroups:  rootlessCg,
	})
	if err != nil {
		return nil, err
	}

	root := context.GlobalString("root")
	return libcontainer.Create(root, id, config) // 得到了一个 Container 结构体
}
```

## 处理container console io
我们知道docker一般有 `-i`, `-t`, `-d` 选项和console io有关
- -i 交互模式：容器共享父进程的stdin/stdout/stderr
- -t 打开一个伪终端: 伪终端的意义就是将stdin/stdout变得不再是一个输入输出流，而是像一个真的终端一点，支持控制字符之类的，比如退格键和方向键，比如显示颜色 
- -d detach：容器在后台运行，不占用当前终端

```

// setupIO modifies the given process config according to the options.
func setupIO(process *libcontainer.Process, container *libcontainer.Container, createTTY, detach bool, sockpath string) (*tty, error) {
    // -t 对应 createTTY
	if createTTY {
		process.Stdin = nil // 清空进程的标准输入输出
		process.Stdout = nil
		process.Stderr = nil
		t := &tty{}
		if !detach {
			if err := t.initHostConsole(); err != nil { // 从 stderr, stdout, stdin 中找到一个有效的console(tty)，因为有可能当前进程并没有attach一个console
				return nil, err
			}
			parent, child, err := utils.NewSockPair("console")
			if err != nil {
				return nil, err
			}
			process.ConsoleSocket = child
			t.postStart = append(t.postStart, parent, child) // io.closer
			t.consoleC = make(chan error, 1) // 这个就是一个简单的wait信号了，console channel
			go func() {
				t.consoleC <- t.recvtty(parent)
			}()
		} else {
			// the caller of runc will handle receiving the console master
			conn, err := net.Dial("unix", sockpath)
			if err != nil {
				return nil, err
			}
			uc, ok := conn.(*net.UnixConn)
			if !ok {
				return nil, errors.New("casting to UnixConn failed")
			}
			t.postStart = append(t.postStart, uc)
			socket, err := uc.File()
			if err != nil {
				return nil, err
			}
			t.postStart = append(t.postStart, socket)
			process.ConsoleSocket = socket // 如果指定了detach，又想分配tty，就得指定一个socket path
		}
		return t, nil
	}
	// when runc will detach the caller provides the stdio to runc via runc's 0,1,2
	// and the container's process inherits runc's stdio.
	if detach {
        // 直接继承runc进程的stdio，可以和 setupProcessPipes 对比， setupProcessPipes是新建pipe，在runc进程的stdio之间拷贝
        // 直接继承的原因是什么？
		inheritStdio(process) // 使用runc进程的stdio, 也就是os.stdout, os.stdin, os.stderr
		return &tty{}, nil
	}

	config := container.Config()
	rootuid, err := config.HostRootUID() // rootless相关配置
	if err != nil {
		return nil, err
	}
	rootgid, err := config.HostRootGID() // rootless相关配置
	if err != nil {
		return nil, err
	}

    // 如果既没有tty，也没有detach，进入这里
	return setupProcessPipes(process, rootuid, rootgid)
}


// setup pipes for the process so that advanced features like c/r are able to easily checkpoint
// and restore the process's IO without depending on a host specific path or device
func setupProcessPipes(p *libcontainer.Process, rootuid, rootgid int) (*tty, error) {
	i, err := p.InitializeIO(rootuid, rootgid) 创建 os.Pipe, w端挂在process上，r端挂在i，i将会被下面的代码使用
    // 这里要新创建一个os.Pipe，而不是直接继承runc进程的stdio的原因是什么？可能是怕多进程写同一个pipe写坏了?
	if err != nil {
		return nil, err
	}
	t := &tty{
		closers: []io.Closer{
			i.Stdin,
			i.Stdout,
			i.Stderr,
		},
	}
	// add the process's io to the post start closers if they support close
	for _, cc := range []interface{}{
		p.Stdin,
		p.Stdout,
		p.Stderr,
	} {
		if c, ok := cc.(io.Closer); ok {
			t.postStart = append(t.postStart, c)
		}
	}
	go func() {
		_, _ = io.Copy(i.Stdin, os.Stdin) // 一直copy直到 stdin EOF
		_ = i.Stdin.Close() // stdin 不用 t.copyIO 是因为copy完后要关闭w端
	}()
	t.wg.Add(2)
	go t.copyIO(os.Stdout, i.Stdout) // copy完后关闭读端, 一直copy直到EOF
	go t.copyIO(os.Stderr, i.Stderr)
	return t, nil
}


```


## init process
在start的核心逻辑 `container.start(process)` 中，通过 `parent, err := c.newParentProcess(process)` 创建出parentProcess, 这里的 parentProcess 有两种，initProcess 或 setnsProcess（这里其实叫做 ProcessControler 好一点，会由这个controler启动子进程，并和子进程交互）   
简化后如下:
```
cmd := exec.Command("/proc/self/exe", "init") // `runc init`
cmd.Args[0] = os.Args[0]
cmd.Stdin = p.Stdin
cmd.Stdout = p.Stdout
cmd.Stderr = p.Stderr
cmd.Dir = c.config.Rootfs

// ...

// 创建 ipc socket pair (这里不创建os.Pipe, 而是uds, 因为uds是双向的，更灵活，管道是单向的)
var (
	comm processComm
	err  error
)
comm.initSockParent, comm.initSockChild, err = utils.NewSockPair("init") // initSock(或者是initPipe, 代码里面是混用的) 作用是 parentProcess和childProcess进行交互，传递childProcess的real pid 和 用户自定义命令等
if err != nil {
	return nil, fmt.Errorf("unable to create init pipe: %w", err)
}
comm.syncSockParent, comm.syncSockChild, err = newSyncSockpair("sync")
if err != nil {
	return nil, fmt.Errorf("unable to create sync pipe: %w", err)
}
comm.logPipeParent, comm.logPipeChild, err = os.Pipe()
if err != nil {
	return nil, fmt.Errorf("unable to create log pipe: %w", err)
}
return &comm, nil

// ...

if p.Init {
	// We only set up fifoFd if we're not doing a `runc exec`. The historic
	// reason for this is that previously we would pass a dirfd that allowed
	// for container rootfs escape (and not doing it in `runc exec` avoided
	// that problem), but we no longer do that. However, there's no need to do
	// this for `runc exec` so we just keep it this way to be safe.
	if err := c.includeExecFifo(cmd); err != nil {
		return nil, fmt.Errorf("unable to setup exec fifo: %w", err)
	}
	
	return c.newInitProcess(p, cmd, comm)
	//	init := &initProcess{
	//		containerProcess: containerProcess{
	//			cmd:           cmd, // runc init
	//			comm:          comm, // 几个通信的uds
	//			manager:       c.cgroupManager,
	//			config:        c.newInitConfig(p), // 里面是 childProcess 用户进程的命令，如果是initProcess，这里是config.json 里的command
	//			process:       p,
	//			bootstrapData: data,
	//			container:     c,
	//		},
	//		intelRdtManager: c.intelRdtManager,
	//	}
	//	c.initProcess = init
}
return c.newSetnsProcess(p, cmd, comm)
//	proc := &setnsProcess{
//		containerProcess: containerProcess{
//			cmd:           cmd, // runc init
//			comm:          comm, // 几个通信的uds
//			manager:       c.cgroupManager,
//			config:        c.newInitConfig(p),// 里面是process 用户进程的命令，如果是setnsProcess，这里是 runc exec -it $container $command
//			process:       p,
//			bootstrapData: data,
//			container:     c,
//		},
//		cgroupPaths:     state.CgroupPaths,
//		rootlessCgroups: c.config.RootlessCgroups,
//		intelRdtPath:    state.IntelRdtPath,
//		initProcessPid:  state.InitProcessPid,
//	}
```


## Container
我们看看`container`有哪些操作：
```
// 启动容器，也就是启动 parentProcess，可能是 initProcess 也可能是 setnsProcess (实例化一个processControler后拉起childProcess)
func (c *Container) Start(process *Process) error {}


func (c *Container) Run(process *Process) error {}
func (c *Container) Exec() error {}

// 设置容器的配置，比如cgroup配置（可以用于running态容器调整资源）
func (c *Container) Set(config configs.Config) error {}

// runc进程创建parent进程（parent进程包含两种:initProcess 和 setnsProcess ）
func (c *Container) newParentProcess(p *Process) (parentProcess, error) {}

// 容器的init进程的controller，当调用runc create后被调用，实例化的process controler将拉起子进程启动init进程，随后原地exec成用户主进程
func (c *Container) newInitProcess(p *Process, cmd *exec.Cmd, comm *processComm) (*initProcess, error) {}

// 容器的setns进程的controller，当调用runc exec $command 后被调用，实例化的process controler将拉起子进程启动init进程，随后原地exec成$command进程
func (c *Container) newSetnsProcess(p *Process, cmd *exec.Cmd, comm *processComm) (*setnsProcess, error) {}

```

## parentProcess
parentProcess 是个interface， 可能的实现是initProcess或者setnsProcess, 这里的parentProcess 可以理解成一个process controller，负责拉起子进程并和子进程交互。
```
type parentProcess interface {
	// pid returns the pid for the running process.
	pid() int

	// start starts the process execution.
	start() error

	// send a SIGKILL to the process and wait for the exit.
	terminate() error

	// wait waits on the process returning the process state.
	wait() (*os.ProcessState, error)

	// startTime returns the process start time.
	startTime() (uint64, error)
	signal(os.Signal) error
	externalDescriptors() []string
	setExternalDescriptors(fds []string)
	forwardChildLogs() chan error
}
```

### initProcess Controller

#### parentProcess
```
// 启动 `runc init` 进程
// err := p.cmd.Start() 
// 传递 NewNetlinkRequest, 这里使用NetLink结构，因为netlink结构是内核支持的，后面调用系统调用时会比较方便
// if _, err := io.Copy(p.comm.initSockParent, p.bootstrapData); err != nil {
//    return fmt.Errorf("can't copy bootstrap data to pipe: %w", err)
// }
// 通过initSock获取最终子进程initProcess的pid （子进程在cgo里面的nsexec函数里面经过了多次clone，这里拿到最终的子进程）
// childPid, err := p.getChildPid()
// 等待直接子进程退出, 然后将 initProcess 设置为待管理的最终子进程
// if err := p.waitForChildExit(childPid); err != nil {
//   return fmt.Errorf("error waiting for our first child to exit: %w", err)
// }
// 对childPid创建Mount配置：这里的request是个往requestCh发送数据的fn，在 goCreateMountSources 中创建了requestCh，并异步消费requestCh用于mount
// request, cancel, err := p.goCreateMountSources(context.Background())
// 对childPid创建网络配置
// p.createNetworkInterfaces()
// 向initSock 发送用户进程相关的配置，比如用户进程的启动命令
// utils.WriteJSON(p.comm.initSockParent, p.config)
// loop 处理子进程发送过来的一些信息，比如 procMountPlease 请求挂载路径，procSeccomp 暂时没看懂是在干嘛，似乎只是往 seccomp 的listenerPath发送了点东西，  procReady 代表container created成功， procHooks 代表runc可以执行一些hooks了，比如Prestart、CreateRuntime
// parseSync(p.comm.syncSockParent, func(sync *syncT) error {})
// 读到EOF或处理error后，关闭socket写端，读端会收到EOF
// p.comm.syncSockParent.Shutdown(unix.SHUT_WR)
func (p *initProcess) start() (retErr error) {}
```

#### childProcess端
runc会创建出 `runc init` 子进程, 这个进程会先调用cgo里面的nsexec函数, clone出多个子进程（clone了两次，用于setns等），最终子进程会调用 `return system.Exec(name, l.config.Args, l.config.Env)` 原地执行用户自定义命令。
```
// 可以看到 `init` command 没有注册在main.go, 而是注册在 init func 里
// 原因其实比较简单，是因为使用的cli库没有提供一种ignore参数，如果cli库允许注册某种command，但是不展示在help信息里，那么作为内部command的init，也可以注册在main.go 里，而不用hack在init func 里。
func init() {
	if len(os.Args) > 1 && os.Args[1] == "init" {
		// This is the golang entry point for runc init, executed
		// before main() but after libcontainer/nsenter's nsexec().
		libcontainer.Init()
	}
}

// libcontainer:
func Init() {
	runtime.GOMAXPROCS(1)
	runtime.LockOSThread()

	if err := startInitialization(); err != nil {
		// If the error is returned, it was not communicated
		// back to the parent (which is not a common case),
		// so print it to stderr here as a last resort.
		//
		// Do not use logrus as we are not sure if it has been
		// set up yet, but most important, if the parent is
		// alive (and its log forwarding is working).
		fmt.Fprintln(os.Stderr, err)
	}
	// Normally, StartInitialization() never returns, meaning
	// if we are here, it had failed.
	os.Exit(255) // 可以看到这里直接退出了，不会进入main 函数
}

// Normally, this function does not return. If it returns, with or without an
// error, it means the initialization has failed. If the error is returned,
// it means the error can not be communicated back to the parent.
func startInitialization() (retErr error) {
	// Get the synchronisation pipe.
	envSyncPipe := os.Getenv("_LIBCONTAINER_SYNCPIPE")
	syncPipeFd, err := strconv.Atoi(envSyncPipe)
	if err != nil {
		return fmt.Errorf("unable to convert _LIBCONTAINER_SYNCPIPE: %w", err)
	}
	syncPipe := newSyncSocket(os.NewFile(uintptr(syncPipeFd), "sync"))
	defer syncPipe.Close()

	defer func() {
		// If this defer is ever called, this means initialization has failed.
		// Send the error back to the parent process in the form of an initError
		// if the sync socket has not been closed.
		if syncPipe.isClosed() {
			return
		}
		ierr := initError{Message: retErr.Error()}
		if err := writeSyncArg(syncPipe, procError, ierr); err != nil {
			fmt.Fprintln(os.Stderr, err)
			return
		}
		// The error is sent, no need to also return it (or it will be reported twice).
		retErr = nil
	}()

	// Get the INITPIPE.
	envInitPipe := os.Getenv("_LIBCONTAINER_INITPIPE")
	initPipeFd, err := strconv.Atoi(envInitPipe)
	if err != nil {
		return fmt.Errorf("unable to convert _LIBCONTAINER_INITPIPE: %w", err)
	}
	initPipe := os.NewFile(uintptr(initPipeFd), "init")
	defer initPipe.Close()

	// Set up logging. This is used rarely, and mostly for init debugging.

	// Passing log level is optional; currently libcontainer/integration does not do it.
	if levelStr := os.Getenv("_LIBCONTAINER_LOGLEVEL"); levelStr != "" {
		logLevel, err := strconv.Atoi(levelStr)
		if err != nil {
			return fmt.Errorf("unable to convert _LIBCONTAINER_LOGLEVEL: %w", err)
		}
		logrus.SetLevel(logrus.Level(logLevel))
	}

	logFd, err := strconv.Atoi(os.Getenv("_LIBCONTAINER_LOGPIPE"))
	if err != nil {
		return fmt.Errorf("unable to convert _LIBCONTAINER_LOGPIPE: %w", err)
	}
	logPipe := os.NewFile(uintptr(logFd), "logpipe")

	logrus.SetOutput(logPipe)
	logrus.SetFormatter(new(logrus.JSONFormatter))
	logrus.Debug("child process in init()")

	// Only init processes have FIFOFD.
	var fifoFile *os.File
	// 这里initType 就两种类型：standard、setns，starndard表示initProcess
	envInitType := os.Getenv("_LIBCONTAINER_INITTYPE")
	it := initType(envInitType)
	if it == initStandard {
		// fifofd 是 exec.fifo 文件，是个fifo命名管道，用于通知initProcess 是否可以调用system.exec 执行用户主进程
		fifoFd, err := strconv.Atoi(os.Getenv("_LIBCONTAINER_FIFOFD"))
		if err != nil {
			return fmt.Errorf("unable to convert _LIBCONTAINER_FIFOFD: %w", err)
		}
		fifoFile = os.NewFile(uintptr(fifoFd), "initfifo")
	}

	var consoleSocket *os.File
	if envConsole := os.Getenv("_LIBCONTAINER_CONSOLE"); envConsole != "" {
		console, err := strconv.Atoi(envConsole)
		if err != nil {
			return fmt.Errorf("unable to convert _LIBCONTAINER_CONSOLE: %w", err)
		}
		consoleSocket = os.NewFile(uintptr(console), "console-socket")
		defer consoleSocket.Close()
	}

	var pidfdSocket *os.File
	if envSockFd := os.Getenv("_LIBCONTAINER_PIDFD_SOCK"); envSockFd != "" {
		sockFd, err := strconv.Atoi(envSockFd)
		if err != nil {
			return fmt.Errorf("unable to convert _LIBCONTAINER_PIDFD_SOCK: %w", err)
		}
		pidfdSocket = os.NewFile(uintptr(sockFd), "pidfd-socket")
		defer pidfdSocket.Close()
	}

	// From here on, we don't need current process environment. It is not
	// used directly anywhere below this point, but let's clear it anyway.
	os.Clearenv()

	defer func() {
		if err := recover(); err != nil {
			if err2, ok := err.(error); ok {
				retErr = fmt.Errorf("panic from initialization: %w, %s", err2, debug.Stack())
			} else {
				retErr = fmt.Errorf("panic from initialization: %v, %s", err, debug.Stack())
			}
		}
	}()

	// 在这里阻塞读runc进程发送过来的init数据，比如用户进程命令啥的
	var config initConfig
	if err := json.NewDecoder(initPipe).Decode(&config); err != nil {
		return err
	}

	// If init succeeds, it will not return, hence none of the defers will be called.
	return containerInit(it, &config, syncPipe, consoleSocket, pidfdSocket, fifoFile, logPipe)
}
```

```
i := &linuxStandardInit{
	pipe:          pipe, // sync socket, 用于和 parentProcess(也就是runc) 交互
	consoleSocket: consoleSocket, // console socket
	pidfdSocket:   pidfdSocket, // childProcess 创建出来后, 发送childProcess的pid到socket，这个是用户自己建出来的socket，不是runc内部的。在parentProcess中open，继承给childProcess
	parentPid:     unix.Getppid(), // parentProcess(也就是runc)的pid
	config:        config, // 从initPipe 读到的config, 包含用户自定义命令等信息
	fifoFile:      fifoFile, // exec.fifo 文件, initProcess 特有，用于作为一种信号通知，告知initProcess可以从created变成running(即调用system.exec 原地替换成用户主进程)
	logPipe:       logPipe, // 日志pipe，日志将被parentProcess消费
}
```

## fd继承
如果通过`fork`, 那当然就直接继承了打开的fd，如果是通过`*exec.Cmd`（或者就是一般说的调用子进程的方式（本质上是fork+exec））, 在go语言的处理上，是通过`cmd.ExtraFiles`, 比如 `cmd.ExtraFiles = append(cmd.ExtraFiles, fifo)`  

```
ExtraFiles specifies additional open files to be inherited by the new process. It does not include standard input, standard output, or standard error. If non-nil, entry i becomes file descriptor 3+i.

ExtraFiles is not supported on Windows.

field ExtraFiles []*os.File
```

子进程使用该描述符时，其fd编号从3开始（因为0、1、2是内置的），比如ExtraFiles[0]的fd是3，ExtraFiles[1]的编号是4  

很显然，我们比较难知道ExtraFiles[0]到底是个啥，所以runc中会通过环境变量传递：
```
fifoName := filepath.Join(c.stateDir, execFifoFilename)
fifo, err := os.OpenFile(fifoName, unix.O_PATH|unix.O_CLOEXEC, 0)
cmd.ExtraFiles = append(cmd.ExtraFiles, fifo)
stdioFdCount := 3
cmd.Env = append(cmd.Env,
		"_LIBCONTAINER_FIFOFD="+strconv.Itoa(stdioFdCount+len(cmd.ExtraFiles)-1))
```

子进程通过`os.NewFile(fd, $name)`得到`*os.File`, name 随便取。
```
fifoFd, err := strconv.Atoi(os.Getenv("_LIBCONTAINER_FIFOFD"))
if err != nil {
	return fmt.Errorf("unable to convert _LIBCONTAINER_FIFOFD: %w", err)
}
fifoFile = os.NewFile(uintptr(fifoFd), "initfifo")
```


# start
当执行create命令后, initProcess 会阻塞在 fifo 管道上，直到有另一个进程打开管道
```
fd, err := unix.Open(fifoPath, unix.O_WRONLY|unix.O_CLOEXEC, 0)
if err != nil {
	return &os.PathError{Op: "open exec fifo", Path: fifoPath, Err: err}
}
if _, err := unix.Write(fd, []byte("0")); err != nil {
	return &os.PathError{Op: "write exec fifo", Path: fifoPath, Err: err}
}

// ...

// 执行用户主进程
return system.Exec(name, l.config.Args, l.config.Env)
```

当执行start命令时，作用只是打开并读取一下 fifo 管道（这里的读取内容没啥实际信息，可能是为了并发考虑，如果并发调用start，前一个会成功，后一个会失败）
```
func (c *Container) exec() error {
// ...
	blockingFifoOpenCh := awaitFifoOpen(path)
// ...
}
```

# exec
在runc的设计中，exec和create的差别不大，都有parentProcess和childProcess的概念，只不过从parent/childProcess的意义上将，一个是initProcess，一个是setnsProcess, 但毫无疑问，流程都是差不多的，因为initProcess就是执行用户主进程，setnsProcess就是执行用户自定义命令。  
initProcess需要执行所有的初始化操作，比如rootfs，各种ns，网络路由等，setns只需要进入对应的ns即可。  

# nsexec
在拉起childProcess的过程中，有一个很关键的技术，`nsexec()`, 这是一个c写的代码, 用于在程序启动时自动进入特定Linux命名空间。
可以看到，cgo的init函数里执行了 `nsexec()`, 这个 `nsexec()` 将会在 go 的所有代码（全局变量、init函数、main函数）之前执行，
> __attribute__((constructor)) 是GCC特性，标记 init() 函数在 ​共享库加载时自动执行。
> 当Go程序启动时，C代码作为共享库加载，init() 会立即调用 nsexec()
```
//go:build linux && !gccgo

package nsenter

/*
#cgo CFLAGS: -Wall
extern void nsexec();
void __attribute__((constructor)) init(void) {
	nsexec();
}
*/
import "C"

```

当正常使用 runc 时，nsexec会直接退出：
```
pipenum = getenv_int("_LIBCONTAINER_INITPIPE");
if (pipenum < 0) {
	/* We are not a runc init. Just return to go runtime. */
	return;
}
```

当执行`runc init`时，也就是childProcess时，nsexec正常执行， 完成了 childProcess 的ns设置(`err = setns(ns->fd, type);`)，并进行了多次clone：
```
// 当前在stage-0 进程

// 初始化几个pipe
int sync_child_pipe[2], sync_grandchild_pipe[2];
socketpair(AF_LOCAL, SOCK_STREAM, 0, sync_child_pipe)
socketpair(AF_LOCAL, SOCK_STREAM, 0, sync_grandchild_pipe)

switch (setjmp(env)) {
case STAGE_PARENT:{
	// 子进程直接跳到 STAGE_CHILD 执行
	// CLONE_PARENT 参数表示clone出兄弟进程，而非子进程
	stage1_pid = clone(()=>{longjmp(env, STAGE_CHILD)}, ca.stack_ptr, CLONE_PARENT | SIGCHLD, &ca); 
	
	syncfd = sync_child_pipe[1];
	close(sync_child_pipe[0])

	stage1_complete = false;
	while (!stage1_complete) {
		// 处理 syncfd 传递过来的 stage-1 的:
		// 1. SYNC_USERMAP_PLS(更新进程的uid/gid map: e.g. write_file(map, map_len, "/proc/%d/gid_map", pid)) 
		// 2. SYNC_RECVPID_PLS(收到stage-1进程发送来的stage2_pid) , 并将stage1_pid, stage2_pid 发送给initPipe, 在parentProcess中会wait stage0_pid/stage1_pid, 并将真实的pid设置为stage2_pid
		// 3. SYNC_TIMEOFFSETS_PLS 设置容器时间相对物理机的偏移量，这是一种time namepsace
		// 4. SYNC_CHILD_FINISH：stage1_complete=true
	}

	syncfd = sync_grandchild_pipe[1];
	close(sync_grandchild_pipe[0])
	stage2_complete = false;
	while (!stage2_complete) {
		// 向 stage-2 发送信息

		s = SYNC_GRANDCHILD;
		write(syncfd, &s, sizeof(s))
		read(syncfd, &s, sizeof(s))
		if (s != SYNC_CHILD_FINISH){failed}
	}

	// stage-0 进程退出
	exit(0);
}
case STAGE_CHILD:{
	// 当前在stage-1进程

	syncfd = sync_child_pipe[0];
	close(sync_child_pipe[1])

	join_namespaces(config.namespaces)

	if (config.cloneflags & CLONE_NEWUSER) {
		try_unshare(CLONE_NEWUSER, "user namespace"); // 如果是rootless模式，用unshare将当前进程移入 user namespace （如果是让子进程进入user namespace，把CLONE_NEWUSER传给clone就行）
		
		// ...
		
		// 请求stage-0 进行 user mapping， 因为stage-1 进程没权限（具体为啥没权限不清楚，看源码注释是和CLONE_PARENT有关）
		s = SYNC_USERMAP_PLS;
		write(syncfd, &s, sizeof(s))
		read(syncfd, &s, sizeof(s))
		if (s != SYNC_USERMAP_ACK){failed}

		// ...

		setresuid(0, 0, 0) // 将当前进程作为ns里的root，也就是uid=0
	}

	try_unshare(config.cloneflags, "remaining namespaces"); // 注释里有提到，某些内核的clone对一些参数的联合使用有点问题，所以在这里unshare。
	// 当unshare CLONE_PID 时，当前进程的pid仍在原pid ns，其子进程在新的pid namespace, pid = 1

	
	// ...

	// 子进程直接跳到 STAGE_INIT 执行
	stage2_pid = clone(()=>{longjmp(env, STAGE_INIT)}, ca.stack_ptr, CLONE_PARENT | SIGCHLD, &ca);

	s = SYNC_RECVPID_PLS
	write(syncfd, &s, sizeof(s))
	write(syncfd, &stage2_pid, sizeof(stage2_pid))
	read(syncfd, &s, sizeof(s))
	if (s != SYNC_RECVPID_ACK){failed}

	s = SYNC_CHILD_FINISH;
	write(syncfd, &s, sizeof(s))

	// stage-1 进程退出
	exit(0);
}
case STAGE_INIT:{
	syncfd = sync_grandchild_pipe[0];
	close(sync_grandchild_pipe[1]) 
	close(sync_child_pipe[0])

	read(syncfd, &s, sizeof(s))
	if (s != SYNC_GRANDCHILD){failed}

	setsid()
	setuid(0)
	setgid(0)

	s = SYNC_CHILD_FINISH;
	write(syncfd, &s, sizeof(s))
	close(sync_grandchild_pipe[0])
	return;
}
}
```

# FS mount
这里讲一下文件或者rootfs是怎么挂载的

首先，runc bundle要求我们已经准备好了一个rootfs，其次，我们进入一个全新的mount namespace。

## rootfs
1. 对rootfs的mount可以通过chroot或者pivotroot
	1. 如果没有指定 new mount namespace, 那就直接chroot: unix.Chroot("."); unix.Chdir("/"); (这里后面再调用一次chdir，避免rootfs切换后路径没对齐)
	2. 一般来说，都指定了new mount namespace，这时使用 unix.PivotRoot(".", ".")，中间有一些复杂的内核层面的trick，看了一些issue也没太看懂，这里不赘述了。

## bind mount
对于常见的文件/目录挂载，都是通过mount -o bind.  
首先在目标挂载目录创建一个挂载点：
```
destDir, destBase := filepath.Split(dest)
destDirFd, err := utils.MkdirAllInRootOpen(rootfs, destDir, 0o755)
unix.Mknodat(int(destDirFd.Fd()), destBase, unix.S_IFREG|0o644, 0)
```
随后将对应文件或目录的fd对应的文件（形如 /proc/self/fd/111） 挂在目标的fd（形如 /proc/self/fd/112）上：
unix.Mount(src, dst, fstype, flags, data)


# Console IO
tty是怎么创建的，以及怎么生效的，即怎么把某个进程的stdio关联到终端的stdio？
> 如果我们直接在前台调用某个进程，倒是不用担心tty的问题，都会自动继承tty的io，但如果是dockerd/containerd 这种daemon场景呢？


## mount

通过打开 `f = os.OpenFile("/dev/ptmx", unix.O_RDWR|unix.O_NOCTTY|unix.O_CLOEXEC, 0)` 文件，就会拿到一个tty的fd，通过 `unix.Syscall(unix.SYS_IOCTL, f.Fd(), &u, ...)` 系统调用，拿到对应的创建出来的tty的文件地址`fmt.Sprintf("/dev/pts/%d", u)`， 随后，将tty的文件地址mount到 `/dev/console`, 随后打开slavepath，将对应的fd dup到 0、1、2 上，这意味着对0/1/2的重定向  

在这里，存在console的master和slave，master就是打开 `/dev/ptmx` 得到的fd， slave就是 `unix.Syscall(unix.SYS_IOCTL` 得到的 fd
> ​Master → Slave：控制端（如用户键盘输入）发送数据到被控进程。
> ​Slave → Master：被控进程的输出（如命令结果）返回给控制端。
> Master/Slave 之间的数据拷贝是内核自动完成的，基本上来说，只要某个被控进程的stdio被重定向到slave，就正常关联到console的stdio了。我们操作的目的的本质就是怎么把某个进程的stdio关联到终端的stdio。


```
在 new mount namespace 里面执行


// setupConsole sets up the console from inside the container, and sends the
// master pty fd to the config.Pipe (using cmsg). This is done to ensure that
// consoles are scoped to a container properly (see runc#814 and the many
// issues related to that). This has to be run *after* we've pivoted to the new
// rootfs (and the users' configuration is entirely set up).
func setupConsole(socket *os.File, config *initConfig, mount bool) error {
	defer socket.Close()
	// At this point, /dev/ptmx points to something that we would expect. We
	// used to change the owner of the slave path, but since the /dev/pts mount
	// can have gid=X set (at the users' option). So touching the owner of the
	// slave PTY is not necessary, as the kernel will handle that for us. Note
	// however, that setupUser (specifically fixStdioPermissions) *will* change
	// the UID owner of the console to be the user the process will run as (so
	// they can actually control their console).

	pty, slavePath, err := console.NewPty()
	if err != nil {
		return err
	}
	// After we return from here, we don't need the console anymore.
	defer pty.Close()

	if config.ConsoleHeight != 0 && config.ConsoleWidth != 0 {
		err = pty.Resize(console.WinSize{
			Height: config.ConsoleHeight,
			Width:  config.ConsoleWidth,
		})
		if err != nil {
			return err
		}
	}

	// Mount the console inside our rootfs.
	if mount {
		if err := mountConsole(slavePath); err != nil {
			return err
		}
	}
	// While we can access console.master, using the API is a good idea.
	if err := utils.SendRawFd(socket, pty.Name(), pty.Fd()); err != nil {
		return err
	}
	runtime.KeepAlive(pty)

	// Now, dup over all the things.
	return dupStdio(slavePath)
}

// NewPty creates a new pty pair
// The master is returned as the first console and a string
// with the path to the pty slave is returned as the second
func NewPty() (Console, string, error) {
	f, err := openpt()
	if err != nil {
		return nil, "", err
	}
	slave, err := ptsname(f)
	if err != nil {
		return nil, "", err
	}
	if err := unlockpt(f); err != nil {
		return nil, "", err
	}
	m, err := newMaster(f)
	if err != nil {
		return nil, "", err
	}
	return m, slave, nil
}

// openpt allocates a new pseudo-terminal by opening the /dev/ptmx device
func openpt() (*os.File, error) {
	return os.OpenFile("/dev/ptmx", unix.O_RDWR|unix.O_NOCTTY|unix.O_CLOEXEC, 0)
}

// dupStdio opens the slavePath for the console and dups the fds to the current
// processes stdio, fd 0,1,2.
func dupStdio(slavePath string) error {
	fd, err := unix.Open(slavePath, unix.O_RDWR, 0)
	if err != nil {
		return &os.PathError{
			Op:   "open",
			Path: slavePath,
			Err:  err,
		}
	}
	for _, i := range []int{0, 1, 2} {
		if err := unix.Dup3(fd, i, 0); err != nil {
			return err
		}
	}
	return nil
}


// mount initializes the console inside the rootfs mounting with the specified mount label
// and applying the correct ownership of the console.
func mountConsole(slavePath string) error {
	f, err := os.Create("/dev/console")
	if err != nil && !os.IsExist(err) {
		return err
	}
	if f != nil {
		// Ensure permission bits (can be different because of umask).
		if err := f.Chmod(0o666); err != nil {
			return err
		}
		f.Close()
	}
	return mount(slavePath, "/dev/console", "bind", unix.MS_BIND, "")
}
```