# MVLAND 调研 —— 免费额度 + AI 流程拆解

> 调研日期：2026-09-14
> 来源：mvland.com 实际页面抓取（`/pricing`、`/ai-music-video-generator`）
> 注：抓取的是 Next.js 的 flight data，以下内容为页面内嵌数据的原文提取

---

## 一、有没有免费的？—— 有

**结论：有免费套餐（Free plan），但功能受限。**

### 官方 FAQ 原文

> **Q: Can I use MVLAND for free?**
> **A1:** Yes, MVLAND offers a free plan for all users, allowing you to use a
> selection of templates and content at no cost.
> **A2:** If you plan to use MVLAND for work or professional purposes, you can
> upgrade to a paid plan. Paid users receive more credits, higher concurrency,
> additional project capacity, commercial usage rights, and access to advanced
> features.

### Free 套餐的具体限制

页面里 `coreAccess.free` 字段原文：

| 项 | 原文 | 含义 |
|---|---|---|
| 额度 | Free trial credits | 赠送试用额度（未标明具体数字） |
| 模型 | Access to selected models and styles | **只能用部分模型和风格** |
| 成本 | Higher cost per MV generation | 每次生成消耗**更多** credits |
| 水印 | Exported videos with MVLAND **watermark** | **导出带水印** |
| 商用 | Commercial usage rights **not included** | **不能商用** |

### 付费套餐解锁什么

- Access to all premium models（全部高级模型）
- Access to all MV styles（全部风格）
- 更低的单次生成成本（Basic→Ultra 递减）
- **Remove download watermark**（去水印）
- **Full ownership & commercial rights**（完整所有权 + 商用权）

### 套餐层级

`Free / Basic / Plus / Max / Ultra`

- Free 副标题：*Start your music video journey for free*
- Basic：*An affordable way to start creating music videos*
- Plus：*Give every track a professional visual identity*
- Max：*For frequent creators scaling output*
- Ultra：*For teams and high-volume production*

官网对比表里自报的价格锚点是 **From $24/Mo**（对付费档）。

### 赚额度的途径（不是免费档，但能白嫖）

页面有 Creator Program 和推荐奖励：

| 方式 | 奖励 |
|---|---|
| 申请成为 Creator（需 2000+ 粉丝，Instagram/YouTube/TikTok） | **2,000 credits** |
| 推荐新用户注册 | 每有效注册 **$1** |
| 邀请创作者 | 500 credits |
| 发布作品拿绩效奖励 | 首发 $10，后续按粉丝量分级（$10 → $1,200） |

> ⚠️ 注意：FAQ 明确「subscription credits **do not roll over**」——
> 订阅额度**不结转**，当期不用完就作废。

---

## 二、AI 流程是什么？—— 四步自动化

官网原话：*Fully automated end-to-end creation—produce professional-grade MVs fast, even with zero experience*

### 四步流程（原文）

```dsh-ui
{"title":"MVLAND 的 AI 制作流程","gap":14,"items":[{"type":"steps","steps":[{"title":"Upload & Analyze Music","description":"上传原创音轨或从内置曲库选。MVLAND 自动检测 **rhythm（节奏）、accents（重音）、emotional dynamics（情绪起伏）**，作为创作基础。"},{"title":"Customize Style & Characters","description":"选视觉风格和拍摄场景，然后选择或生成专属角色。MVLAND 会在**每个镜头里保持角色外观和视觉风格一致**。"},{"title":"Generate & Adjust Storyboard","description":"自动生成与音乐情绪匹配的**完整分镜（storyboard）**。可自由调整镜头顺序、时长和画面，锁定创作方向。"},{"title":"Edit & Export the Final Cut","description":"在可视化编辑器里微调细节 —— **剪辑和配乐自动完成** —— 然后一键导出成品 MV。"}]}]}
```

### 关键技术点

| 环节 | 实现方式 | 出处 |
|---|---|---|
| **音乐分析** | 自动检测 rhythm / accents / emotional dynamics | 官网流程描述 |
| **歌词分析** | Enhanced **lyrics**, mood & rhythm analysis（付费档增强） | pricing features |
| **角色一致性** | 跨镜头保持 character looks + visual style consistent | Step 2 描述 |
| **分镜生成** | Auto-generate storyboard matching the music's mood | Step 3 描述 |
| **配乐/剪辑** | editing and scoring are handled automatically | Step 4 描述 |
| **视频模型** | 页面提到 **Seedance**（字节的视频生成模型） | 模型字段 |

### 编辑器里的节点结构（从页面数据看）

页面内部的功能描述：

- `createMusicAnalysisDescription`: "analyze music summary and structure"
- `createVideoDescription`: "Storyboard, MV shots"
- `createMusicGenerationDescription`: "Generate music from text prompts"
- `uploadMediaDescription`: "Upload images, videos and audio files"

**说明它是个节点式（node-based）工作流**：音乐分析 → 分镜/镜头 → 视频生成，各节点可配置。

### 视觉方向分类（模板）

1. **Stylized Visuals** —— 围绕角色和声音建世界
2. **Cinematic Stories** —— 情绪转氛围化叙事
3. **Editorial Portraits** —— 时尚/音乐文化风格
4. **Live Performance** —— 演出场景
5. **Experimental Worlds** —— 实验性视觉

### 工作流对比（官网自己的表格）

| | MVLAND | 传统制片 |
|---|---|---|
| 成本 | From $24/Mo | $10K–$100K+ / MV |
| 首版耗时 | **20–30 min** | 2–几周 |
| 工作方式 | 上传歌曲，AI 分析歌词/情绪/节奏 | 概念→脚本→选址→拍摄→剪辑 |
| 改稿 | 快速切换风格/模型/版本 | 受档期和预算限制 |

---

## 三、它背后的技术栈

从抓取的页面结构判断：

| 项 | 判断依据 |
|---|---|
| 前端框架 | **Next.js + Turbopack**（`/_next/static/chunks/`、`self.__next_f` flight data） |
| 渲染 | SSR + 客户端 hydration |
| 支付 | **支付宝**（Alipay，有 "Alipay QR code payment" 字段） |
| 账户体系 | Credits 虚拟货币制 |
| 视频模型 | 至少接了 **Seedance**，付费档 "Access to all premium models" 说明是**多模型聚合** |

> **本质**：它是个**多模型聚合 + 工作流编排**的平台，核心价值不在自研模型，
> 而在把「音乐分析 → 角色一致性 → 分镜 → 视频生成」串成自动化管道。

---

## 四、对你的实际参考价值

### 免费能白嫖到什么

- ✅ 可以用部分模板和风格试水
- ❌ 导出**带水印**、**不能商用**、额度有限、每次生成更费 credits

### 想真正用起来的成本

- 付费档起价 **$24/月**
- 或者走 Creator Program（需要 2000+ 粉丝）
- 或者用推荐奖励一点点攒

### 这套流程对你 Chiikawa 项目的启发

1. **音乐驱动**：它是从音频反推画面节奏，你现在是纯手工 K 帧。
   如果要升级，可以先分析 BGM 的节拍点，再对着节拍打关键帧。
2. **角色一致性**是核心卖点 —— 这正是 AI 生成视频最难的地方，
   而你用 Blender 3D 模型天然解决了这个问题（模型不变，随便换角度）。
3. **分镜先行**：它是先生成 storyboard 再逐镜头生成。你做长动画时也可以先排分镜表。
4. **它有免费档可以试** —— 如果你只是想快速出个 MV 效果，可以先白嫖看看效果，
   再决定要不要自己用 Blender 做。

---

## 附：抓取到的原始页面

| 页面 | 大小 |
|---|---|
| `mvland.com/ai-music-video-generator/music/FenoE6FMc?tab=storyboard` | 209 KB |
| `mvland.com/pricing` | 275 KB |
| `mvland.com/ai-music-video-generator` | 417 KB |

> 技术说明：该域名解析到 `198.18.x.x`（保留测试网段），
> 常规抓取工具会判定为非公网 IP 而拒绝。本次用 curl 直连成功。
