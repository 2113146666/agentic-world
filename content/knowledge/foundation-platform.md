---
id: foundation-platform
title: 工作室底层只保留一条控制面
layer: foundation
category: platform
tags: [platform, ops, files]
summary: 底层是登记、任务包、知识文件和工作台槽位。不另起编排框架。
points:
  - 基础赛道在 registry/agentic-world.yaml。垂类在 content/verticals。角色说明在 content/roles。
  - 知识是 content/knowledge 里的 Markdown。改完执行知识重建，现有前端就能读到。
  - 工作台顺序是灵感、世界观、选择、转化、量化。选择是相对旧四步补上的一步。
  - 新垂类用 python -m agentic_world vertical new。文件会自带产品、技术、测试、运营四个阶段。
  - 模板模式只产空槽位。没有模型密钥时，不伪造正文。
misconceptions:
  - 底层架构不是把五个垂类各做成一套服务。
  - 接受进化提案不会自动改目标文件。
sources:
  - title: registry/agentic-world.yaml
    url: ""
updated: "2026-10-07"
---
