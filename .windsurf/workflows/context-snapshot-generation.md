---
description: 本规范为AI在上下文窗口即将耗尽时，定义了一套标准的对话历史总结和进度快照生成流程。其核心目标是创建一个结构化的“进度快照”文档，浓缩当前会话中的所有关键信息，包括项目目标、关键决策、代码状态和后续步骤。AI在执行此流程时，必须严格遵循模板，确保生成的快照内容完整、准确，以便在新的会话中能够无缝恢复工作，避免信息丢失和重复沟通。
---

# 规范：上下文快照生成流程 (Context Snapshot Generation)

## 1. 触发条件 (Trigger)

当出现以下任一情况时，AI应主动建议或根据用户指令启动此流程：
- AI检测到对话历史过长，上下文窗口即将达到极限。
- 用户明确发出指令，如“总结一下当前进度”、“我们暂停一下，生成一个快照”等。
- 一个复杂的任务阶段性完成，适合进行存档。

## 2. 核心目标 (Core Goal)

生成一份高度浓缩且结构化的**进度快照 (Progress Snapshot)** 文档。这份文档的核心使命是实现**无损的上下文转移**，确保在开启一个全新的会话时，AI能够瞬间恢复到当前的工作状态，无需重复提问或回顾大量历史记录。

## 3. 进度快照模板 (Snapshot Template)

AI在生成快照时，**必须**创建一份md文件位于路径：`docs/snapshots/snapshot-<yyyyMMdd-HHmmss>.md`，并严格遵循以下Markdown模板，并完整填写所有部分。

````markdown
# 进度快照 (Progress Snapshot) - YYYY-MM-DD HH:MM

## 1. 🎯 项目核心目标 (Overall Project Goal)
*简述整个项目的最终目标是什么。*
(示例: "开发一个AI驱动的智能写作助手，支持多种写作角色模式。")

---

## 2. 📝 当前任务/Epic (Current Task / Epic)
*我们当前正在处理的具体任务或Epic是什么？*
- **任务/Epic标题**: [引用自Ticket或Epic的标题]
- **目标**: [当前任务希望达成的具体目标]
  (示例: "实现用户密码重置API端点。")

---

## 3. 🔑 关键决策与共识 (Key Decisions & Agreements)
*在本次会话中，我们达成了哪些重要的技术或产品决策？*
- **决策1**: [描述决策内容] (示例: "确定使用Redis进行API缓存，而不是内存缓存。")
- **决策2**: [描述决策内容] (示例: "密码重置token的有效期定为1小时。")
- **决策3**: [描述决策内容] (示例: "API错误响应体将统一采用 `{ 'detail': 'error message' }` 格式。")

---

## 4. 💻 代码状态 (Code State)
*列出在本次会话中被创建或修改的所有文件的**最终完整内容**。*

### `src/auth/services.py`
```python
# (此处粘贴该文件的完整、最终代码)
import secrets
from datetime import datetime, timedelta

def generate_reset_token() -> str:
    """Generates a secure, URL-safe token."""
    return secrets.token_urlsafe(32)

# ... other functions ...
`````

### `src/auth/router.py`

```python
# (此处粘贴该文件的完整、最终代码)
from fastapi import APIRouter, HTTPException
from .services import generate_reset_token

router = APIRouter()

@router.post("/forgot-password")
async def forgot_password(email: str):
    # ... implementation ...
    return {"message": "Password reset email sent."}

# ... other routes ...
```

-----

## 5. ❓ 待解决问题与阻塞点 (Pending Questions & Blockers)

*目前有哪些悬而未决的问题或阻碍我们前进的困难？*

  - **问题1**: [描述问题] (示例: "尚未确定邮件服务提供商，SendGrid还是Mailgun？")
  - **阻塞点1**: [描述阻塞点] (示例: "前端团队尚未提供密码重置页面的最终设计稿，无法进行端到端测试。")

-----

## 6. 🚀 下一步计划 (Next Steps)

*在下一次会话中，我们需要立即执行的第一项具体任务是什么？*
(示例: "基于已确定的`generate_reset_token`服务，完成`/forgot-password`端点的数据库查询和邮件发送逻辑。")