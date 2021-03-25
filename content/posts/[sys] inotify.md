---
title: "[sys] inotify"
date: 2021-03-25
tags: ["sys"]
categories: ["sys"]
---

# Inotify

> ```
> The inotify API provides a mechanism for monitoring filesystem
> events.  Inotify can be used to monitor individual files, or to
> monitor directories.  When a directory is monitored, inotify will
> return events for the directory itself, and for files inside the
> directory.
> ```

四个API

- func InotifyInit() (fd int, err error)
  - func InotifyInit1(flags int) (fd int, err error) 这个可以设置flags(O_NONBLOCK,O_BLOCK),这涉及到read(fd,buffer,buff_size)时是阻塞还是非阻塞
- func InotifyAddWatch(fd int, pathname string, mask uint32) (watchdesc int, err error)
  - 对pathname进行监听,并绑定到fd上,mask表示监听哪些事件
  - 返回watch desciptor,专用于remove取消监听
- func InotifyRmWatch(fd int, watchdesc uint32) (success int, err error)
  - 将监听事件从fd上取消
- 其他
  - 读取事件
    - read(fd , buf , buf_sz)
  - 关闭监听
    - close(fd)

buf 将需要被解释成:

```c
struct inotify_event {
    int      wd;       /* Watch descriptor */
    uint32_t mask;     /* Mask describing event */
    uint32_t cookie;   /* Unique cookie associating related
                                     events (for rename(2)) */
    uint32_t len;      /* Size of name field */
    char     name[];   /* Optional null-terminated name */
};
```

在go语言中就是:

```go
event := (*syscall.InotifyEvent)(unsafe.Pointer(&buffer[offset]))
```





示例: from: [tomnomnom/go-learning](https://golang.hotexamples.com/zh/site/redirect?url=https%3A%2F%2Fgithub.com%2Ftomnomnom%2Fgo-learning)

```go
func main() {
	fd, err := syscall.InotifyInit()
	if err != nil {
		log.Fatal(err)
	}
	defer syscall.Close(fd)

	wd1, err := syscall.InotifyAddWatch(fd, "test1.log", syscall.IN_ALL_EVENTS)
	wd2, err = syscall.InotifyAddWatch(fd, "../test2.log", syscall.IN_ALL_EVENTS)
	//_, err = syscall.InotifyAddWatch(fd, ".", syscall.IN_ALL_EVENTS)
	if err != nil {
		log.Fatal(err)
	}
	defer syscall.InotifyRmWatch(fd, uint32(wd1))
    defer syscall.InotifyRmWatch(fd, uint32(wd2))

	fmt.Printf("WD is %d\n", wd)

	for {
		// Room for at least 128 events
		buffer := make([]byte, syscall.SizeofInotifyEvent*128)
		bytesRead, err := syscall.Read(fd, buffer)
		if err != nil {
			log.Fatal(err)
		}

		if bytesRead < syscall.SizeofInotifyEvent {
			// No point trying if we don't have at least one event
			continue
		}

		fmt.Printf("Size of InotifyEvent is %s\n", syscall.SizeofInotifyEvent)
		fmt.Printf("Bytes read: %d\n", bytesRead)

		offset := 0
		for offset < bytesRead-syscall.SizeofInotifyEvent {
			event := (*syscall.InotifyEvent)(unsafe.Pointer(&buffer[offset]))
			fmt.Printf("%+v\n", event)

			if (event.Mask & syscall.IN_ACCESS) > 0 {
				fmt.Printf("Saw IN_ACCESS for %+v\n", event)
			}

			// We need to account for the length of the name
			offset += syscall.SizeofInotifyEvent + int(event.Len)
		}
	}

}
```

