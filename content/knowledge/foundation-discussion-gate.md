---
id: foundation-discussion-gate
title: 正式讨论前的外部输入
layer: foundation
category: llm-basics
tags: [gate, discussion]
summary: 提问者先把任务包交给 GPT-6 及以上智力的平台，把返回贴回 review。没有这份输入，任务停在草稿。
points:
  - 用 python -m agentic_world job new 生成任务包，再用 job show --packet 取出全文。
  - 外部平台的返回用 job gate 贴回。贴回之后状态才是 gated。
  - job accept 在缺少 review 时会拒绝写下正式结论。
  - 运维杂务可以加 --no-gate。垂类讨论默认不能跳过。
misconceptions:
  - 门禁不是再开一轮内部聊天。输入必须来自任务包之外的强模型平台。
  - 有了外部输入，也不等于结论已经被接受。
sources:
  - title: content/charter.md
    url: ""
updated: "2026-10-07"
---
