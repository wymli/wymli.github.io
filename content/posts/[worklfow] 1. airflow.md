---
title: "[airflow] airflow"
date: 2025-03-20
categories : ["workflow"]
tags : ["workflow", "airflow"]
---

> 原文记录在飞书文档：https://c6t4wbgxht.feishu.cn/docx/POUfdFT2YoXlbHxeUA2cntmanzc

官方文档很清晰，简单的知识无需赘述：https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html#workloads

# 架构
- Scheduler: 调度器，负责决定dag run的触发和 task instance 的提交
- Executor: 执行器，负责执行task instance, executor本身只是一串在scheduler里的控制面代码
  - 数据面可以是local process执行，也可以是celery，也可以是k8s pod
    - worker可能是预先创建的，也可能是伴生实时创建的，视executor自己决定
  - 所有executor继承自BaseExecutor, 我们可以实现自己的executor
- Dag file processor: dag解析器, 定时解析新的dag file，一般是scheduler进程的一部分，也可以抽出来，工作就是解析文件后更新db。
- Dag file folder: 这个dag文件目录也非常重要，parser/scheduler/task instance 都需要能访问
- webserver： ui
- Metadata db: 用于存储dag file解析后的元数据和各种运行时信息

# 集成airflow

暂时无法在飞书文档外展示此内容
比如模型离线训练场景：
还是很适合的，唯一的问题就是得用python写，不太好维护
- Dag run 触发
  - 设置 schedule_interval=None，关闭按时间触发
  - 使用 TriggerDagRunOperator 来触发dag进行下一次dagrun(可以条件触发，如果训完就不触发)
  - 使用airflow trigger或rest api来进行第一次触发
- 历史训练：
  - 通过CheckpointOperatpr 获取已训练的ckpt的日期，通过 DataCheckerOperator, 进行可用样本的获取和切分，当次训练样本切分结果写入xcom，被后续operator使用
- 追新：和上面一样，没区别
- 多阶段训练：
暂时无法在飞书文档外展示此内容
JobRunner
JobRunner 的启动对应三个命令行，都是启动对应的daemon进程
- airflow dag-processor
- airflow scheduler
- airflow triggerer
- (airflow api-server)(核心进程还有一个apiserver, 不过不属于JobRunner )

具体的操作：
- DagProcessorJob: 
  - _run_parsing_loop：创建dag
- SchedulerJob:
  - _create_dagruns_for_dags：创建dag run
  - _schedule_dag_run：调度dag run，包括创建task instance ，以及将对应的task instance设置为scheduled，可以在下一步入队被执行
  - _critical_section_enqueue_task_instances：从 db 查出 DR.state == DagRunState.RUNNING and TI.state == TaskInstanceState.SCHEDULED 的 TaskInstance, 提交给executor入队 (queue_workload()) 【这里的critical_section是指会以select ... for update 的方式query出来，保证只有一个scheduler执行入队操作, 需要mysql 8+。多scheduler时，直接配置scheduler的deployment的replica个数就行】
- TriggerJob: 
  - 用于负责调度 Deferrable Operator，也就是触发器（比如等待文件存在、等待api响应符合预期等）
  - Deferrable Operator 是 sensor 的升级（相当于SensorAsync），sensor是一种同步阻塞的operator/task， 会占用worker资源。但是Deferrable Operator 可以将sensor的逻辑卸载到trigger，即提交一个trigger，由专门的TriggerJob负责检测是否触发, 是异步的，无需占用worker资源。

# Triggerer
简单的sensor很好理解，和普通的operator没区别，只是运行的是阻塞或轮询的代码而已。当阻塞的逻辑卸载到单独的deferred operator后（也就是trigger），看看是怎么实现的。
sensor和async sensor(trigger)的代码在接口上也没有太大区别：

如何实现一个自定义的sensor:
- 参数里的deferrable 决定了是 sensor，还是 async sensor （这里 deferrable  只是我们自己的参数，对airflow来说，只是是否调用 self.defer的问题，或者说，调用 self.defer 后，内部会 raise TaskDeferred(), 进而被注册到trigger里）
- execute 里可以是阻塞的逻辑，也可以是调用 self.defer() 提交一个trigger

class WaitOneHourSensor(BaseSensorOperator):
    def __init__(self, deferrable: bool = conf.getboolean("operators", "default_deferrable", fallback=False), **kwargs) -> None:
        super().__init__(**kwargs)
        self.deferrable = deferrable
    
    def execute(self, context: Context) -> None:
        if self.deferrable:
            self.defer(
                trigger=TimeDeltaTrigger(timedelta(hours=1)),
                method_name="execute_complete",)
        else:time.sleep(3600)
    def execute_complete(self,context: Context,event: dict[str, Any] | None = None,) -> None:
    # We have no more work to do here. Mark as complete.return
随后，提交的Trigger表记录（不同executor的代码会有区别）：
try:
    TaskInstance._execute_task_with_callbacks(...)
    ti.state = TaskInstanceState.SUCCESS
except TaskDeferred as defer:
    trigger_row = Trigger(
        classpath=ti.task.start_trigger_args.trigger_cls,
        kwargs=trigger_kwargs,
    )
    session.add(trigger_row)
    ti.state = TaskInstanceState.DEFERRED
TriggerJob将检测Trigger表记录，执行里面的trigger_cls，比如TimeDeltaTrigger(timedelta(hours=1))
Executor
Python 没有interface的设计，导致代码里很难看出继承BaseExecutor 后要实现哪些方法，只能一个一个看了
# LocalExecutor

localExecutor 的实现较简单，BaseExecutor的heartbeat() 方法将被周期性调用（实际上，scheduler每一个loop（读db找到待调度的task，入队），就是一次heartbeat），进而调用子实现的sync() 方法，在LocalExecutor 的sync() 方法中，将
- 负责处理resultQueue
  - 这里只是简单的success/failed 状态
- 负责spawnWorkers
  - LocalExecutor的workers是有需要时，才创建出来，创建出来的worker进入while循环阻塞等待 activity_queue , 等到后，会os.fork() 创建子进程执行真正的task
- activity_queue 和 resultQueue 都是os.Pipe, 在多进程之间通信

自定义的executor需要定义如下方法：
class LocalExecutor(BaseExecutor):
    def start(self) -> None: 构造初始化，定义一些实例变量，比如队列
    def sync(self) -> None: 在heartbeat时被调用，可以处理worker数的扩缩容、workload的执行结果写db等，executor自己决定
    def end(self) -> None: 析构，比如销毁队列
    @provide_session
    def queue_workload(self, workload: workloads.All, session: Session = NEW_SESSION):
        workload入队操作
# KubernetesExecutor
KubernetesExecutor 借助了 BaseExecutor 提供的 self.queued_tasks 队列, 所以需要实现更多的方法，如果自己写一个队列，就不用。
可以看到 execute_async() 方法最终还是往 self.task_queue put，所以这里看起来只是多中转了一道，感觉没啥必要，queue_workload的时候，直接往task_queue写就完事了。
`
class KubernetesExecutor(BaseExecutor):
    def start(self) -> None:
    def execute_async(
        self,
        key: TaskInstanceKey,
        command: CommandType,
        queue: str | None = None,
        executor_config: Any | None = None,
    ) -> None:
        kube_executor_config = PodGenerator.from_obj(executor_config)
        self.task_queue.put((key, command, kube_executor_config, pod_template_file))
    def queue_workload(self, workload: workloads.All, session: Session | None) -> None:
        from airflow.executors import workloads

        if not isinstance(workload, workloads.ExecuteTask):
            raise RuntimeError(f"{type(self)} cannot handle workloads of type {type(workload)}")
        ti = workload.ti
        self.queued_tasks[ti.key] = workload
    def _process_workloads(self, workloads: list[workloads.All]) -> None:
        for w in workloads:
            del self.queued_tasks[key]
            self.execute_async(key=key, command=command, queue=queue, executor_config=executor_config)  # type: ignore[arg-type]
            self.running.add(key)
    
    def sync(self) -> None:
         // 处理 results
         while True:
             results = self.result_queue.get_nowait()
             key, state, pod_name, namespace, resource_version = results
             self._change_state(key, state, pod_name, namespace)
         // 处理 create
         for _ in range(self.kube_config.worker_pods_creation_batch_size):
             task = self.task_queue.get_nowait()
             self.kube_scheduler.run_next(task) // build and create pod
`

# Operator
## 注册
当进入Dag上下文时，会将自己push到DagContextStack里，进而可以被找到。当在dag内部实例化operator时，会找到对应的dag，并注册。
使用装饰器时同理（装饰器内部仍然是调用了 with Dag():）。
`
class Dag:
    def __enter__(self) -> Self:
        from airflow.sdk.definitions._internal.contextmanager import DagContext

        DagContext.push(self)
        return self

    def __exit__(self, _type, _value, _tb):
        from airflow.sdk.definitions._internal.contextmanager import DagContext

        _ = DagContext.pop()
 
 class ContextStack(Generic[T], metaclass=ContextStackMeta):
    _context: deque[T]

    @classmethod
    def push(cls, obj: T):
        cls._context.appendleft(obj)

    @classmethod
    def pop(cls) -> T | None:
        return cls._context.popleft()

    @classmethod
    def get_current(cls) -> T | None:
        try:
            return cls._context[0]
        except IndexError:
            return None

class DagContext(ContextStack[DAG]):
    ...

class BaseOperatorMeta(abc.ABCMeta):
    from airflow.sdk.definitions._internal.contextmanager import DagContext, TaskGroupContext

    dag: DAG | None = kwargs.get("dag")
    if dag is None:
        dag = DagContext.get_current()
        if dag is not None:
            kwargs["dag"] = dag
`

## 解析
// childWorker 构造 dagBag
`
for filepath in files_to_parse:
    found_dags = self.process_file(filepath)

def process_file:
    mods = self._load_modules_from_file(filepath, safe_mode)
    found_dags = self._process_modules(filepath, mods, file_last_changed_on_disk)

def _load_modules_from_file:
    // 可以看到，执行了一遍module，进而使 @dag @task 等装饰器生效
    loader = importlib.machinery.SourceFileLoader(mod_name, filepath)
    spec = importlib.util.spec_from_loader(mod_name, loader)
    new_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = new_module
    loader.exec_module(new_module)
    return [new_module]

def _process_modules:
    // 寻找最高层的dag加入
    top_level_dags = {(o, m) for m in mods for o in m.__dict__.values() if isinstance(o, DAG)}
    for dag, mod in top_level_dags:
        self.bag_dag(dag=dag)
`

## 执行
在executor拉起task instance 后，需要执行对应的operator或者叫task。
- LocalExecutor:
  - Worker子进程（控制面）拉起ChildWorker子进程（数据面）（worker只会至多控制一个childworker）, 通过stdin传入数据
`
msg = StartupDetails.model_construct(
    ti=ti,
    dag_rel_path=os.fspath(dag_rel_path),
    bundle_info=bundle_info,
    requests_fd=self._requests_fd,
    ti_context=ti_context,
    start_date=start_date,
)
self.stdin.write(msg.model_dump_json().encode())
self.stdin.write(b"\n")
  - 子进程执行 _subprocess_main, 
def _subprocess_main():
    from airflow.sdk.execution_time.task_runner import main

    main()

def main():
    execute = functools.partial(task.resume_execution, next_method=next_method, next_kwargs=kwargs)
    with timeout(timeout_seconds):
        result = ctx.run(execute, context=context)

def resume_execution:
    execute_callable = getattr(self, next_method)
    return execute_callable(context, **next_kwargs)
- KubernetestExecutor
command = [
    "python",
    "-m",
    "airflow.sdk.execution_time.execute_workload",
    "/tmp/execute/input.json",
]
`

// /tmp/execute/input.json 通过 init container 写入，要是我，就直接环境变量了
`
// /tmp/execute 是个emptydir
// escaped_json 的内容是 shlex.quote(workload.model_dump_json(exclude={"ti": {"executor_config"}}))

input_file_path = "/tmp/execute/input.json"
init_container = k8s.V1Container(
    name="init-container",
    image="busybox",
    command=["/bin/sh", "-c", f"echo {escaped_json} > {input_file_path}"],
    volume_mounts=[execute_volume_mount],
)
`

// airflow.sdk.execution_time.execute_workload 相比于 LocalExecutor 只是 workload 初始化时不一样，执行时还是调用了：
`
supervise(
    # This is the "wrong" ti type, but it duck types the same. TODO: Create a protocol for this.
    ti=workload.ti,  # type: ignore[arg-type]
    dag_rel_path=workload.dag_rel_path,
    bundle_info=workload.bundle_info,
    token=workload.token,
    server=conf.get("core", "execution_api_server_url"),
    log_path=workload.log_path,
    # Include the output of the task to stdout too, so that in process logs can be read from via the
    # kubeapi as pod logs.
    subprocess_logs_to_stdout=True,
)
`