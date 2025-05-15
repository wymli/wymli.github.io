---
title: "[Go] release notes"
date: 2025-05-10
categories : ["golang"]
tags : ["golang"]
---

> 原文我记录在飞书文档: https://c6t4wbgxht.feishu.cn/docx/Nu9sd0FobokaxMxEddxc9VTXnIg
> 拷贝时会有格式问题

Eino 是字节开源的golang写的 ai agent 开发框架，类似python写的langchain、llamaindex。
Ai agent 智能体，可以理解为是一种完成 “感知、思考、执行” 的程序，其中思考的部分借助大模型完成
大模型有三种主要的应用模式：
1. 直接对话
2. 知识库 RAG
3. AI Agent 工具调用

针对三种主要应用模式，Eino有如下几种组件抽象：
1. 对话：
  1. ChatTemplate
  2. ChatModel
2. 知识库：
  1. 文本加载和处理：Document.Loader, Document.Transformer
  2. 文本编码：Embedding （调用大模型编码）
  3. 向量存储：Indexer
  4. 召回：Retriever
3. AI Agent决策执行：
  1. ToolsNode
4. 自定义组件：
  1. Lambda：自己实现具体的逻辑
# Quick Start
## Chat
按照官方示例，简单改了下，有如下的代码，一个极简的嵌入预置prompt和对话的例子：
流程也很简单：
1. 创建prompt tmpl
2. 渲染prompt tmpl得到 inputMessages
3. 创建chatModel
4. 调用chatModel，将inputMessages传入
  1. ChatModel是不同大语言模型的抽象接口
```
type ChatModel interface {
    // 获得完整输出
    Generate(ctx context.Context, input []*schema.Message, opts ...Option) (*schema.Message, error)
    // 逐个token输出
    Stream(ctx context.Context, input []*schema.Message, opts ...Option) (
        *schema.StreamReader[*schema.Message], error)

    // BindTools bind tools to the model.
    // BindTools before requesting ChatModel generally.
    // notice the non-atomic problem of BindTools and Generate.
    BindTools(tools []*schema.ToolInfo) error
}
```
```
/*
 * Copyright 2024 CloudWeGo Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package main

import (
    "context"
    "io"
    "iter"
    "log"

    "github.com/cloudwego/eino-ext/components/model/ollama"
    "github.com/cloudwego/eino/components/prompt"
    "github.com/cloudwego/eino/schema"
)


func main() {
    ctx := context.Background()

    // 创建模板，使用 FString 格式
    tmpl := prompt.FromMessages(schema.FString,
        // 系统消息模板
        schema.SystemMessage("你是一个{role}。你需要用{style}的语气回答问题。你的目标是帮助程序员保持积极乐观的心态，提供技术建议的同时也要关注他们的心理健康。"),

        // 插入需要的对话历史（新对话的话这里不填）
        schema.MessagesPlaceholder("chat_history", true),

        // 用户消息模板
        schema.UserMessage("问题: {question}"),
    )

    // 使用模板生成消息
    messages, err := tmpl.Format(context.Background(), map[string]any{
        "role":     "程序员鼓励师",
        "style":    "积极、温暖且专业",
        "question": "我的代码一直报错，感觉好沮丧，该怎么办？",
        // 对话历史（这个例子里模拟两轮对话历史）
        "chat_history": []*schema.Message{
            schema.UserMessage("你好"),
            schema.AssistantMessage("嘿！我是你的程序员鼓励师！记住，每个优秀的程序员都是从 Debug 中成长起来的。有什么我可以帮你的吗？", nil),
            schema.UserMessage("我觉得自己写的代码太烂了"),
            schema.AssistantMessage("每个程序员都经历过这个阶段！重要的是你在不断学习和进步。让我们一起看看代码，我相信通过重构和优化，它会变得更好。记住，Rome wasn't built in a day，代码质量是通过持续改进来提升的。", nil),
        },
    })
    if err != nil {
        log.Fatalf("format template failed: %v\n", err)
    }

    // 连接ollma并创建chatModel
    // 简单安装一下ollma就行: curl -fsSL https://ollama.com/install.sh | sh
    // 然后下载模型：ollama pull llama2
    chatModel, err := ollama.NewChatModel(ctx, &ollama.ChatModelConfig{
        BaseURL: "http://localhost:11434", // Ollama 服务地址
        Model:   "llama2",                 // 模型名称
    })
    if err != nil {
        log.Fatalf("create ollama chat model failed: %v", err)
    }

    result, err := chatModel.Generate(ctx, messages)
    if err != nil {
        log.Fatalf("llm generate failed: %v", err)
    }
    log.Printf("result: %s\n\n", JsonIndent(result))

    streamResult, err := chatModel.Stream(ctx, messages)
    if err != nil {
        log.Fatalf("llm generate failed: %v", err)
    }

    for msg, iterInfo := range NewStreamResultIter(streamResult) {
        log.Printf("message[%d]: %+v, err=%v\n", iterInfo.I, msg, iterInfo.Err)
    }
}

func JsonIndent(v any) string {
    x, _ := json.MarshalIndent(v, "", "\t")
    return *(*string)(unsafe.Pointer(&x))
}

type IterInfo struct {
    I   int
    Err error
}

func NewStreamResultIter(sr *schema.StreamReader[*schema.Message]) iter.Seq2[*schema.Message, IterInfo] {
    return func(yield func(*schema.Message, IterInfo) bool) {
        defer sr.Close()

        i := 0
        for {
            message, err := sr.Recv()
            if err == io.EOF {
                return
            }
            if !yield(message, IterInfo{i, err}) {
                return
            }

            i++
        }
    }
}
```
## AI Agent
熟记 “感知-思考-执行”，感知就是提供给大模型一些上下文，思考就是大模型调用，执行就是大模型执行函数调用。应用于ai agent的大模型需要支持函数调用。比如在ollama里，会以tools标记。
流程也不复杂：
1. 编写tool
2. 将tool注册到chatModel
3. 构建toolNode
4. 构建chain
5. 将toolNode添加到chain
6. 编译chain
7. 调用chain
```
import toolutils "github.com/cloudwego/eino/components/tool/utils"
type CreateTodoOpts struct {
    Content string `json:"content,omitempty" jsonschema:"description=content of the todo"`
    EndTime int64  `json:"end_time,omitempty" jsonschema:"description=deadline of the todo"`
}

func (p *CreateTodoOpts) Invoke(_ context.Context, params *CreateTodoOpts) (string, error) {
    logs.Infof("invoke tool create_todo: %+v", params)
    // biz logic
    return `{"msg": "create todo success"}`, nil
}

func main(){
    // 构建tool
    createTool, err := toolutils.InferTool("create_todo", "Create a todo item, eg: content,end_time...", (&CreateTodoOpts{}).Invoke)
    if err != nil {
        logs.Errorf("InferTool failed, err=%v", err)
        return
    }
    
    tools := []tool.BaseTool{
        createTool,
    }
    
    // 将 tools 绑定到 ChatModel
    err = chatModel.BindTools(lo.Map(todoTools, func(v tool.BaseTool, _ int) *schema.ToolInfo {
        info, _ := v.Info(ctx)
        return info
    }))
    if err != nil {
        logs.Errorf("BindTools failed, err=%v", err)
        return
    }
    
    // 构建 toolsNode 节点
    todoToolsNode, err := compose.NewToolNode(ctx, &compose.ToolsNodeConfig{
        Tools: todoTools,
    })
    if err != nil {
        logs.Errorf("NewToolNode failed, err=%v", err)
        return
    }

    // 构建完整的处理链
    chain := compose.NewChain[[]*schema.Message, []*schema.Message]()
    chain.
        AppendChatModel(chatModel, compose.WithNodeName("chat_model")).
        AppendToolsNode(todoToolsNode, compose.WithNodeName("tools"))

    // 编译并运行 chain
    agent, err := chain.Compile(ctx)
    if err != nil {
        logs.Errorf("chain.Compile failed, err=%v", err)
        return
    }
    
    resp, err := agent.Invoke(ctx, []*schema.Message{{...}})
    if err != nil {
        logs.Errorf("agent.Invoke failed, err=%v", err)
        return
    }
}
```
# Graph/Chain/Workflow
Graph: low-level 的类型，需要操作节点和边
Chain: high-level 的类型，底层操作graph, pregel 模式。chain的典型操作是直接append，不断的级联操作，一往无前，无法形成环操作（但是ai agent的开发中，比如ReAct就是环），默认是
Workflow：high-level 的类型，底层操作graph, dag 模式。不支持环。AllPredecessor 语义

chain和workflow 主要是在执行时获取下一批待执行节点时有区别，

# Component
注意区分节点，和挂在节点上的invokeFunc!

## Tools
compose.ToolsNode
这是一个图节点，存放tools。
1. 为什么是toolsNode而不是toolNode？
  1. 和大模型函数调用机制有关，在大模型函数调用里，是大模型返回需要调用的函数名和函数参数，我们自己再去调用，所以我们需要知道有哪些函数可以被调用，那当然是都放在一个node里来查找了。
ToolsNode.Invoke
图节点接收一个input *schema.Message, 返回多个*schema.Message
也比较合理，message里的ToolCalls是个列表，可能有多个函数调用被触发，对于每个触发的函数调用，都添加到返回值里
```
(tn *ToolsNode) Invoke(ctx context.Context, input *schema.Message,opts ...ToolsNodeOption) ([]*schema.Message, error)

tool.InvokableTool / StreamableTool 
在eino中，tool被定义为一种interface：
// BaseTool get tool info for ChatModel intent recognition.
type BaseTool interface {
    // info方法返回参数结构体的json schema，被用于大模型的function call注册
    Info(ctx context.Context) (*schema.ToolInfo, error)
}

// InvokableTool the tool for ChatModel intent recognition and ToolsNode execution.
// nolint: byted_s_interface_name
type InvokableTool interface {
    BaseTool

    // InvokableRun call function with arguments in JSON format
    // InvokableRun或StreamableRun 是实际执行的函数，里面会调用用户传入的函数。
    // 需要注意的是 InvokableRun 接受 argumentsInJSON string参数，而我们定义的是结构体，所以中间会发送序列化操作，框架内部完成该序列化
    // 本质上来说，大模型的在tool_calls字段里的响应肯定是string的，这里InvokableRun就是直接接收大模型的输出，或者说上个节点的输出
    InvokableRun(ctx context.Context, argumentsInJSON string, opts ...Option) (string, error)
}

// StreamableTool the stream tool for ChatModel intent recognition and ToolsNode execution.
// nolint: byted_s_interface_name
type StreamableTool interface {
    BaseTool

    StreamableRun(ctx context.Context, argumentsInJSON string, opts ...Option) (*schema.StreamReader[string], error)
}
```
eino提供了两种方法创建tool:
- tool.NewTool
  - 传入参数结构schema和对应的处理函数
- toolutils.InferTool
  - 传入参数结构体（schema写在注解中）和对应的处理函数
由于tool是一种interface，显然我们也可以自己实现：custom struct impl interface

# 吃透ReAct
```
/*
 * Copyright 2024 CloudWeGo Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package react

import (
    "context"
    "io"

    "github.com/cloudwego/eino/components/model"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/flow/agent"
    "github.com/cloudwego/eino/schema"
)

type state struct {
    Messages                 []*schema.Message
    ReturnDirectlyToolCallID string
}

const (
    nodeKeyTools = "tools"
    nodeKeyModel = "chat"
)

// MessageModifier modify the input messages before the model is called.
type MessageModifier func(ctx context.Context, input []*schema.Message) []*schema.Message

// AgentConfig is the config for ReAct agent.
type AgentConfig struct {
    // ToolCallingModel is the chat model to be used for handling user messages with tool calling capability.
    // This is the recommended model field to use.
    ToolCallingModel model.ToolCallingChatModel

    // Deprecated: Use ToolCallingModel instead.
    Model model.ChatModel

    // ToolsConfig is the config for tools node.
    ToolsConfig compose.ToolsNodeConfig

    // MessageModifier.
    // modify the input messages before the model is called, it's useful when you want to add some system prompt or other messages.
    MessageModifier MessageModifier

    // MaxStep.
    // default 12 of steps in pregel (node num + 10).
    MaxStep int `json:"max_step"`

    // Tools that will make agent return directly when the tool is called.
    // When multiple tools are called and more than one tool is in the return directly list, only the first one will be returned.
    ToolReturnDirectly map[string]struct{}

    // StreamOutputHandler is a function to determine whether the model's streaming output contains tool calls.
    // Different models have different ways of outputting tool calls in streaming mode:
    // - Some models (like OpenAI) output tool calls directly
    // - Others (like Claude) output text first, then tool calls
    // This handler allows custom logic to check for tool calls in the stream.
    // It should return:
    // - true if the output contains tool calls and agent should continue processing
    // - false if no tool calls and agent should stop
    // Note: This field only needs to be configured when using streaming mode
    // Note: The handler MUST close the modelOutput stream before returning
    // Optional. By default, it checks if the first chunk contains tool calls.
    // Note: The default implementation does not work well with Claude, which typically outputs tool calls after text content.
    // Note: If your ChatModel doesn't output tool calls first, you can try adding prompts to constrain the model from generating extra text during the tool call.
    StreamToolCallChecker func(ctx context.Context, modelOutput *schema.StreamReader[*schema.Message]) (bool, error)
}

// Deprecated: This approach of adding persona involves unnecessary slice copying overhead.
// Instead, directly include the persona message in the input messages when calling Generate or Stream.
//
// NewPersonaModifier add the system prompt as persona before the model is called.
// example:
//
//  persona := "You are an expert in golang."
//  config := AgentConfig{
//      Model: model,
//      MessageModifier: NewPersonaModifier(persona),
//  }
//  agent, err := NewAgent(ctx, config)
//  if err != nil {return}
//  msg, err := agent.Generate(ctx, []*schema.Message{{Role: schema.User, Content: "how to build agent with eino"}})
//  if err != nil {return}
//  println(msg.Content)
func NewPersonaModifier(persona string) MessageModifier {
    return func(ctx context.Context, input []*schema.Message) []*schema.Message {
        res := make([]*schema.Message, 0, len(input)+1)

        res = append(res, schema.SystemMessage(persona))
        res = append(res, input...)
        return res
    }
}

func firstChunkStreamToolCallChecker(_ context.Context, sr *schema.StreamReader[*schema.Message]) (bool, error) {
    defer sr.Close()

    for {
        msg, err := sr.Recv()
        if err == io.EOF {
            return false, nil
        }
        if err != nil {
            return false, err
        }

        if len(msg.ToolCalls) > 0 {
            return true, nil
        }

        if len(msg.Content) == 0 { // skip empty chunks at the front
            continue
        }

        return false, nil
    }
}

const (
    GraphName     = "ReActAgent"
    ModelNodeName = "ChatModel"
    ToolsNodeName = "Tools"
)

// Agent is the ReAct agent.
// ReAct agent is a simple agent that handles user messages with a chat model and tools.
// ReAct will call the chat model, if the message contains tool calls, it will call the tools.
// if the tool is configured to return directly, ReAct will return directly.
// otherwise, ReAct will continue to call the chat model until the message contains no tool calls.
// e.g.
//
//  agent, err := ReAct.NewAgent(ctx, &react.AgentConfig{})
//  if err != nil {...}
//  msg, err := agent.Generate(ctx, []*schema.Message{{Role: schema.User, Content: "how to build agent with eino"}})
//  if err != nil {...}
//  println(msg.Content)
type Agent struct {
    runnable         compose.Runnable[[]*schema.Message, *schema.Message]
    graph            *compose.Graph[[]*schema.Message, *schema.Message]
    graphAddNodeOpts []compose.GraphAddNodeOpt
}

// NewAgent creates a ReAct agent that feeds tool response into next round of Chat Model generation.
//
// IMPORTANT!! For models that don't output tool calls in the first streaming chunk (e.g. Claude)
// the default StreamToolCallChecker may not work properly since it only checks the first chunk for tool calls.
// In such cases, you need to implement a custom StreamToolCallChecker that can properly detect tool calls.
func NewAgent(ctx context.Context, config *AgentConfig) (_ *Agent, err error) {
    var (
        chatModel       model.BaseChatModel
        toolsNode       *compose.ToolsNode
        toolInfos       []*schema.ToolInfo
        toolCallChecker = config.StreamToolCallChecker
        messageModifier = config.MessageModifier
    )

    if toolCallChecker == nil {
        toolCallChecker = firstChunkStreamToolCallChecker
    }

    if toolInfos, err = genToolInfos(ctx, config.ToolsConfig); err != nil {
        return nil, err
    }

    if chatModel, err = agent.ChatModelWithTools(config.Model, config.ToolCallingModel, toolInfos); err != nil {
        return nil, err
    }

    if toolsNode, err = compose.NewToolNode(ctx, &config.ToolsConfig); err != nil {
        return nil, err
    }

    graph := compose.NewGraph[[]*schema.Message, *schema.Message](compose.WithGenLocalState(func(ctx context.Context) *state {
        return &state{Messages: make([]*schema.Message, 0, config.MaxStep+1)}
    }))

    // 图的IO格式是（[]*schema.Message, *schema.Message）， 所以 modelPreHandle 的输入必须是[]*schema.Message
    modelPreHandle := func(ctx context.Context, input []*schema.Message, state *state) ([]*schema.Message, error) {
        // 注意 model 节点的前置节点可以是用户输入START, 也可以是工具节点，不过没关系，工具节点的输出也是 []*schema.Message，类型是对的上的
        // 这里可以回忆下，工具节点的签名一般是（*schema.Message,[]*schema.Message）, 业务一个message可能调用多个function call
        state.Messages = append(state.Messages, input...)

        if messageModifier == nil {
            return state.Messages, nil
        }

        modifiedInput := make([]*schema.Message, len(state.Messages))
        copy(modifiedInput, state.Messages)
        return messageModifier(ctx, modifiedInput), nil
    }

    if err = graph.AddChatModelNode(nodeKeyModel, chatModel, compose.WithStatePreHandler(modelPreHandle), compose.WithNodeName(ModelNodeName)); err != nil {
        return nil, err
    }

    if err = graph.AddEdge(compose.START, nodeKeyModel); err != nil {
        return nil, err
    }

    toolsNodePreHandle := func(ctx context.Context, input *schema.Message, state *state) (*schema.Message, error) {
        state.Messages = append(state.Messages, input)
        // 存储 ReturnDirectlyToolCallID 以便于能在后续节点中找到对应的function的callID（一个工具节点可能调用很多个function）
        // 我感觉如果message有个字段是function_name, 其实就解决了
        state.ReturnDirectlyToolCallID = getReturnDirectlyToolCallID(input, config.ToolReturnDirectly)
        return input, nil
    }
    if err = graph.AddToolsNode(nodeKeyTools, toolsNode, compose.WithStatePreHandler(toolsNodePreHandle), compose.WithNodeName(ToolsNodeName)); err != nil {
        return nil, err
    }

    modelPostBranchCondition := func(_ context.Context, sr *schema.StreamReader[*schema.Message]) (endNode string, err error) {
        // 分支条件，决定工具节点是指向模型节点，还是指向 DirectReturn 节点
        if isToolCall, err := toolCallChecker(ctx, sr); err != nil {
            return "", err
        } else if isToolCall {
            return nodeKeyTools, nil
        }
        return compose.END, nil
    }

    // 注意，指向End时，需要使用NewStreamGraphBranch，因为我们将使用Stream模式调用ReactAgent
    // 这里如果不用Stream，当然也行，Eino会帮我们进行Stream/Batch的转换，但是就不是流式输出了
    if err = graph.AddBranch(nodeKeyModel, compose.NewStreamGraphBranch(modelPostBranchCondition, map[string]bool{nodeKeyTools: true, compose.END: true})); err != nil {
        return nil, err
    }

    if len(config.ToolReturnDirectly) > 0 {
        if err = buildReturnDirectly(graph); err != nil {
            return nil, err
        }
    } else if err = graph.AddEdge(nodeKeyTools, nodeKeyModel); err != nil {
        return nil, err
    }

    compileOpts := []compose.GraphCompileOption{compose.WithMaxRunSteps(config.MaxStep), compose.WithNodeTriggerMode(compose.AnyPredecessor), compose.WithGraphName(GraphName)}
    runnable, err := graph.Compile(ctx, compileOpts...)
    if err != nil {
        return nil, err
    }

    return &Agent{
        runnable:         runnable,
        graph:            graph,
        graphAddNodeOpts: []compose.GraphAddNodeOpt{compose.WithGraphCompileOptions(compileOpts...)},
    }, nil
}

func buildReturnDirectly(graph *compose.Graph[[]*schema.Message, *schema.Message]) (err error) {
    // 注意 directReturn 的签名，比较有意思 （*schema.StreamReader[[]*schema.Message] ，*schema.StreamReader[*schema.Message]） ，directReturn节点的前置节点是工具节点，签名是[]*schema.Message，所以这里写*schema.StreamReader[[]*schema.Message]或者 []*schema.Message应该都行，因为图倾向流式输出，所以输出是*schema.StreamReader[*schema.Message]，Eino内部会做批流的类型处理
    directReturn := func(ctx context.Context, msgs *schema.StreamReader[[]*schema.Message]) (*schema.StreamReader[*schema.Message], error) {
        return schema.StreamReaderWithConvert(msgs, func(msgs []*schema.Message) (*schema.Message, error) {
            var msg *schema.Message
            err = compose.ProcessState[*state](ctx, func(_ context.Context, state *state) error {
                for i := range msgs {
                    if msgs[i] != nil && msgs[i].ToolCallID == state.ReturnDirectlyToolCallID {
                        msg = msgs[i]
                        return nil
                    }
                }
                return nil
            })
            if err != nil {
                return nil, err
            }
            if msg == nil {
                return nil, schema.ErrNoValue
            }
            return msg, nil
        }), nil
    }

    nodeKeyDirectReturn := "direct_return"
    if err = graph.AddLambdaNode(nodeKeyDirectReturn, compose.TransformableLambda(directReturn)); err != nil {
        return err
    }

    // this branch checks if the tool called should return directly. It either leads to END or back to ChatModel
    err = graph.AddBranch(nodeKeyTools, compose.NewStreamGraphBranch(func(ctx context.Context, msgsStream *schema.StreamReader[[]*schema.Message]) (endNode string, err error) {
        msgsStream.Close()

        err = compose.ProcessState[*state](ctx, func(_ context.Context, state *state) error {
            if len(state.ReturnDirectlyToolCallID) > 0 {
                endNode = nodeKeyDirectReturn
            } else {
                endNode = nodeKeyModel
            }
            return nil
        })
        if err != nil {
            return "", err
        }
        return endNode, nil
    }, map[string]bool{nodeKeyModel: true, nodeKeyDirectReturn: true}))
    if err != nil {
        return err
    }

    return graph.AddEdge(nodeKeyDirectReturn, compose.END)
}

func genToolInfos(ctx context.Context, config compose.ToolsNodeConfig) ([]*schema.ToolInfo, error) {
    toolInfos := make([]*schema.ToolInfo, 0, len(config.Tools))
    for _, t := range config.Tools {
        tl, err := t.Info(ctx)
        if err != nil {
            return nil, err
        }

        toolInfos = append(toolInfos, tl)
    }

    return toolInfos, nil
}

func getReturnDirectlyToolCallID(input *schema.Message, toolReturnDirectly map[string]struct{}) string {
    if len(toolReturnDirectly) == 0 {
        return ""
    }

    for _, toolCall := range input.ToolCalls {
        if _, ok := toolReturnDirectly[toolCall.Function.Name]; ok {
            return toolCall.ID
        }
    }

    return ""
}

// Generate generates a response from the agent.
func (r *Agent) Generate(ctx context.Context, input []*schema.Message, opts ...agent.AgentOption) (*schema.Message, error) {
    return r.runnable.Invoke(ctx, input, agent.GetComposeOptions(opts...)...)
}

// Stream calls the agent and returns a stream response.
func (r *Agent) Stream(ctx context.Context, input []*schema.Message, opts ...agent.AgentOption) (output *schema.StreamReader[*schema.Message], err error) {
    return r.runnable.Stream(ctx, input, agent.GetComposeOptions(opts...)...)
}

// ExportGraph exports the underlying graph from Agent, along with the []compose.GraphAddNodeOpt to be used when adding this graph to another graph.
func (r *Agent) ExportGraph() (compose.AnyGraph, []compose.GraphAddNodeOpt) {
    return r.graph, r.graphAddNodeOpts
}
```

# 图执行
```
nextTasks, result, err = r.calculateNextTasks(ctx, []*task{{
    nodeKey: START,
    call:    r.inputChannels,
    output:  input,
}}, isStream, cm, optMap) // 计算出下一批任务，从全量节点map中找到 inputChannel 非空的节点（实际实现和graph类型有关，如果是pregel，只支持 AnyPredecessor 模式，也就是任一个依赖完成，当前节点就可以运行）
for step := 0; ; step++ {
        // Check for context cancellation.
        select {
        case <-ctx.Done():
            _ = tm.waitAll()
            return nil, newGraphRunError(fmt.Errorf("context has been canceled: %w", ctx.Err()))
        default:
        }
        if !r.dag && step >= maxSteps {
            return nil, newGraphRunError(ErrExceedMaxSteps)
        }

        // 1. submit next tasks
        // 2. get completed tasks
        // 3. calculate next tasks

        err = tm.submit(nextTasks) // 异步或同步的提交一批任务
        if err != nil {
            return nil, newGraphRunError(fmt.Errorf("failed to submit tasks: %w", err))
        }
        var completedTasks []*task
        completedTasks = tm.wait() // 默认是 wait one, 也就是说一个节点好之后，开始下一轮主循环
        
        
        // ...
        nextTasks, result, err = r.calculateNextTasks(ctx, completedTasks, isStream, cm, optMap)
        // ...
}
func (t *taskManager) submit(tasks []*task) error {
    // ...
    for _, currentTask := range tasks {
        t.num += 1
        go t.execute(currentTask)
    }
    // ...
}

func (t *taskManager) execute(currentTask *task) {
    defer func() {
        panicInfo := recover()
        if panicInfo != nil {
            currentTask.output = nil
            currentTask.err = safe.NewPanicErr(panicInfo, debug.Stack())
        }

        t.done.Send(currentTask)
    }()

    ctx := initNodeCallbacks(currentTask.ctx, currentTask.nodeKey, currentTask.call.action.nodeInfo, currentTask.call.action.meta, t.opts...)
    currentTask.output, currentTask.err = t.runWrapper(ctx, currentTask.call.action, currentTask.input, currentTask.option...)
}

func (t *taskManager) wait() []*task {
    if t.needAll {
        return t.waitAll()
    }

    ta, success := t.waitOne()
    if !success {
        return []*task{}
    }

    return []*task{ta}
}
```
## passthrough 节点
在AnyPredecessor 语义执行时，任一前置节点会触发后续节点执行
对于如下的图：
a -> b -> c
a -> c
当a执行完后，b和c会一起执行，肯定不符合预期，所以需要在a->c 直接插入 passthrough (actually nop) 节点，等一回合再执行

# 内部隐式类型转换：
- 如果上下游节点的流类型无法匹配。 Eino会自动完成 流化、合包 两个操作
  - 流化(Streaming)：将 T 流化成单 Chunk 的 Stream[T]
  - 合包(Concat)：将 Stream[T] 合并成一个完整的 T。
- 如果一个节点要接收多个节点的输出（即AllPredessor模式），那么需要将输出定义成Map, 以方便合并输出
