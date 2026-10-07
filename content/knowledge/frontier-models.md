---
id: frontier-model-ownership
title: 开闭源模型先写清评测再谈选型
layer: frontier
category: models
tags: [models, eval, open-weight]
summary: 模型赛道负责架构和评测记录。没有评测记录的选型不进入正式结论。
points:
  - 一次比较至少写清任务、输入、成功标准和失败样例。
  - 开源与闭源可以并存。漫剧垂类要求先选定本次主路径，不在同一次产出里两套并行铺开。
  - 没有 API 密钥时，系统模式是 agentic_world_template，只保留槽位。
  - 有密钥时，job draft 可以要一版草稿，草稿不会自动变成已接受结论。
misconceptions:
  - 接上模型不等于工作台会自己把小说、漫剧或交易建议写完。
  - 模型卡上的成本档不能代替这次任务的失败样例。
sources:
  - title: registry/agentic-world.yaml
    url: ""
updated: "2026-10-07"
---
