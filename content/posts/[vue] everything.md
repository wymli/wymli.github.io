---
title: "[vue] everything"
date: 2021-03-25
tags: ["vue"]
categories: ["vue"]
---

# 1. vue的生命周期/运行流程/渲染流程/初始化流程
[doc link](https://cn.vuejs.org/v2/guide/instance.html#%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E5%9B%BE%E7%A4%BA)
- vue的入口文件可以有四个可能的命名:main.js,index.js,app.vue,App.vue
  - 真正的入口文件取决于哪个文件包含了vue实例(new Vue({})),渲染流程从vue实例开始
- 流程大致如下:
  - new Vue({})
  - init event
  - 回调 beforeCreate()
  - init element
  - 回调 created()
  - 检查Vue实例:
    - 是否有{el:"..."}?
      - 没有:等待vm.$mount(el)被调用,然后下一步
        - 例: `new Vue({render: h => h(App),}).$mount('#app')`
        - 一般出现在main.js,index.js文件中
      - 有:下一步
    - 是否有\<template>
      - 有:把\<template>编译到render function
      - 没有:把el的outerHTML作为template编译
  - 回调 beforeMount()
  - 创建vm.\$el,并且用vm.\$el替换#el(应该指渲染,用前面的renderFunc/template)
  - 回调 mounted()
    - 实例进入监听循环,当数据被改变时,重新渲染
      - 回调: beforeUpdate()
      - 回调: updated()
  - 当vm.$destroy()被调用
    - 回调: beforeDestroy()
    - teardown(拆除) watchers,子组件,事件监听器
    - 回调: destroyed()

- 分析:
  - vue实例一定要挂载到一个html元素上
  - 手动使用vm.$mount("#app"),是为了延迟挂载渲染
  - render:h=>h(oneComponent) 是一种渲染组件的方式
  ```js
  render: function (createElement) {
    return createElement(App);
  }
  ``` 
## 使用vue-cli,vue create hello-word生成的代码分析
- main.js
```js
import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

new Vue({
  render: h => h(App),
}).$mount('#app')

```
等价于,`...就是把字典解包`
```js
import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

new Vue({
  el: '#app',
  ...App
})
```