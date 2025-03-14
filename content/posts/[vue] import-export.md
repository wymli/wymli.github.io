---
title: "[vue] import-export"
date: 2021-03-25
tags: ["Vue"]
categories: ["Vue"]
---

# About import and export
- 这是es6的语法,即js的语法
- export用于对外输出本模块的数据
- import用于引入其他模块的数据
## 语法细则
```js
// 导出变量
// 法一
// js1
export var name = "a"
// js2
import {name} from "./js1.js"

// 法二
// js1
var name1 = "a"
var name2 = "b"
export {name1 , name2}
// 或者
export name1
export name2
// 或者
export var name1 = "a"
export var name2 = "b"

// js2
import {name1 , name2} from "./js1.js"
// 或者
import {name1} from "./js1.js"
import {name2} from "./js1.js"

// ===========================

// 导出函数,和变量是一致的
function add(x,y){
  return (x+y)
}
export {add}
// 或者
export function add(x,y){
  return x+y
}
// js2
import {add} from "./js1.js"

```

## export and export default
- export,export default均可用于导出变量,函数,文件,模块等
- 一个文件或模块中,export/import可以有多个,但是export default只能有一个
- export的导出,import时要加入{},但是export default则不需要
- export default相当于指定默认输出,而export时,import要完整写出对应导出的变量/函数名
```js
export default {
	address：'1',
}
export var title = '2'
export var zzz = '3'
// js2
import js1,{title as t , zzz} from "./js1.js"
```

## import的后缀名省略
- 直接使用`import js from "./js1"`
- 规则:
  - 在 `webpack.base.conf.js` 中设置
  - 可以省略js,vue后缀
  - 若同时存在js,vue后缀同名文件,js>vue
  - from后可以是文件夹
    - 加载规则:
      - 先看该文件夹有没有packag.json
        - 若有:取package.main指定的js作为from的来源
      - index.js
      - index.vue
  - 注意,一般来说 package.json都只会出现项目根目录,注意不是@,是@的再外面一层,用来配置npm install这些指令
