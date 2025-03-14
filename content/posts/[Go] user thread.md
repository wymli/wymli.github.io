---
title: "[Go] user thread"
date: 2021-03-25
tags: ["Golang"]
categories: ["Golang"]
---

# 用户线程与核心线程

ref: [Scheduler Activations: Effective Kernel Support for the  User-Level Management of Parallelism](https://flint.cs.yale.edu/cs422/doc/sched-act.pdf)

论文观点:

1.  We  argue  that  the  performance  of  user-levelthreads  is  inherently  better  than  that  of  kernel  threads,  rather  than  thisbeing  an  artifact  of  existing  implementations. 
2. kernel   threads   are   the wrong   abstraction   on   which   to   support   user-level management   of   parallelism.   

## 1.用户线程的优势

1. The  cost  of  accessing  thread  management  operations. 