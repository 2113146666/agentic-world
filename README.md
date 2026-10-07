# Agentic World

这是 Agentic World 的控制面，给现有前端 `agentic-world-front` 用。知识、分工、垂类和任务都落在文件里。接口只负责把这些文件读出来，并接上原来的工作台。

基础赛道和垂类以 `registry/agentic-world.yaml` 与 `content/verticals/` 为准。代码、接口和页面不写、不展示负责人姓名。

## 开工时固定发生的两件事

1. 每个任务包的开头都是 `content/charter.md`：第一性原理、奥卡姆剃刀、最终自动化和自进化。
2. 正式讨论前，提问者把任务包交给 GPT-6 及以上智力的平台，把返回贴回来。没有这份输入，写不下正式结论。

四个垂类角色是产品、技术、测试、运营。它们是角色说明，不是四个自动互聊的进程。

## 和现有前端的关系

前端已经定义了这些接口：知识列表和检索、灵感、世界观、转化、量化、`/api/status`。本服务实现同一组路径，并补上原来没有的「选择」。

没有 `OPENAI_API_KEY` 时，`llm_mode` 是 `agentic_world_template`。工作台只产结构槽位，不伪造正文。金融报告的信号和下单列表保持为空，并带风险声明。

## 启动

```bash
cd agentic-world
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest tests.test_agentic_world
python -m agentic_world serve
```

前端在 `agentic-world-front/agentic-world-front` 执行 `npm run dev`。开发服会把 `/api` 代理到 `127.0.0.1:8000`。

## 连续产出时只做这几件事

新增一条知识：在 `content/knowledge` 放一个 Markdown，文首写 `id`、`title`、`layer`、`category`、`tags`、`summary`、`points`、`updated`。然后：

```bash
python -m agentic_world knowledge
```

或在前端 Wiki 里点「重建索引」。分类必须已经出现在赛道或垂类里。`venues` 是留给顶会方向的现成分类。

开一个正式讨论：

```bash
python -m agentic_world job new --domain novel --role product --intent "这条灵感要不要做成可选择的支线"
python -m agentic_world job show <id> --packet
python -m agentic_world job gate <id> --review "这里贴外部平台的返回"
python -m agentic_world job accept <id> --artifact "成功标准：两条支线都还在，人物卡有名字"
```

`--review` 和 `--artifact` 可以用 `@文件路径`。

新增一个垂类：

```bash
python -m agentic_world vertical new --id audio --name 音频 --category audio --focus "先做一条可重复的声音工序"
```

这会写一个带四个角色的工作流文件。前端侧栏要显示中文名时，再把分类补进前端的 `CATEGORY_LABELS`。

改进已有契约：

```bash
python -m agentic_world evolve propose --target content/roles/tech.md --role test --reason "完成标准太宽" --change "要求写出可重复命令"
python -m agentic_world evolve accept <id>
```

接受提案只记一条日志，不改目标文件。

## 目录

| 路径 | 作用 |
| --- | --- |
| `content/charter.md` | 每次任务前面的原则和门禁 |
| `registry/agentic-world.yaml` | 人和基础赛道 |
| `content/verticals` | 小说、漫剧、游戏、金融、热点 |
| `content/roles` | 产品、技术、测试、运营 |
| `content/knowledge` | 给 Wiki 读的条目 |
| `data/` | 任务、工作台产物、进化日志，不提交 |

工作台顺序：灵感 → 世界观 → 选择 → 转化 → 量化。选择的接口是 `POST /api/select/choose`。现有前端还没有这一页，接口已经留好。
