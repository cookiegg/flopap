# AI解读数据模型说明

## 概述

本文档说明了论文AI解读相关的数据模型结构和使用方式。

## 数据模型

### 1. PaperInterpretation（主要AI解读表）

**表名**: `paper_interpretations`

**用途**: 存储论文的AI解读内容

**字段说明**:
- `id`: UUID主键
- `paper_id`: 关联的论文ID（外键，唯一）
- `interpretation`: AI解读内容（Text，markdown格式）
- `language`: 解读语言（默认"zh"）
- `model_name`: 生成解读的AI模型名称

**数据格式**:
- **93.6%** 的记录使用标准markdown格式（`## 标题`）
- **6.4%** 的记录使用兼容的结构化文本格式
- 所有记录都适合TTS语音合成（需清理markdown标记）
- 内容长度控制在 **800-1200字符** 范围内

**标准结构**:
```markdown
## 研究背景
[背景与动机内容]

## 核心方法
[方法与创新内容]

## 主要贡献
[结果与影响内容]
```

**使用示例**:
```python
from app.models import PaperInterpretation
from app.services.content_generation.tts_generate import clean_markdown_for_tts

# 获取AI解读
interpretation = session.query(PaperInterpretation).filter_by(paper_id=paper_id).first()

# 获取原始markdown内容（用于前端显示）
markdown_content = interpretation.interpretation

# 获取TTS清理后的内容（用于语音合成）
tts_content = clean_markdown_for_tts(interpretation.interpretation)
```

### 2. PaperTranslation（翻译表）

**表名**: `paper_translations`

**用途**: 存储论文的中文翻译

**字段说明**:
- `id`: UUID主键
- `paper_id`: 关联的论文ID（外键，唯一）
- `title_zh`: 论文标题中文翻译
- `summary_zh`: 论文摘要中文翻译
- `ai_interpretation`: **已废弃** - 请使用PaperInterpretation表
- `infographic_html`: 信息图HTML内容
- `model_name`: 翻译使用的AI模型名称

**重要提示**: 
- `ai_interpretation`字段已废弃，仅保留用于历史数据兼容
- 新的AI解读应存储在`PaperInterpretation`表中

### 3. PaperTTS（TTS音频表）

**表名**: `paper_tts`

**用途**: 存储论文AI解读的TTS音频文件元数据

**字段说明**:
- `id`: UUID主键
- `paper_id`: 关联的论文ID（外键）
- `file_path`: 音频文件相对路径（基于`backend/data/tts/`）
- `file_size`: 文件大小（字节）
- `voice_model`: 使用的语音模型（默认"zh-CN-XiaoxiaoNeural"）
- `content_hash`: 内容哈希（用于去重和缓存）
- `generated_at`: 音频生成时间

**存储策略**:
- **元数据存储在数据库**中
- **音频文件存储在文件系统**中（`backend/data/tts/`）
- 使用UUID命名音频文件，避免冲突

**使用示例**:
```python
from app.models import PaperTTS

# 获取TTS记录
tts = session.query(PaperTTS).filter_by(paper_id=paper_id).first()

# 获取完整文件路径
full_path = tts.get_full_path()

# 检查文件是否存在
if tts.file_exists():
    print(f"音频文件大小: {tts.file_size_mb:.2f} MB")
```

## 数据流程

### AI解读生成流程

1. **生成AI解读**
   ```python
   from app.services.ai_interpretation_unified import generate_ai_interpretation_unified
   
   interpretation_text = generate_ai_interpretation_unified(client, paper)
   ```

2. **保存到数据库**
   ```python
   from app.models import PaperInterpretation
   
   interpretation = PaperInterpretation(
       paper_id=paper.id,
       interpretation=interpretation_text,
       language="zh",
       model_name="deepseek-chat"
   )
   session.add(interpretation)
   session.commit()
   ```

3. **生成TTS音频**
   ```python
   from app.services.content_generation.tts_generate import generate_tts_for_paper
   
   tts_record = generate_tts_for_paper(paper_id, session)
   ```

### TTS生成流程

1. **获取AI解读内容**
2. **清理markdown标记**（使用`get_tts_content()`方法）
3. **调用edge-tts生成音频**
4. **保存音频文件到文件系统**
5. **保存元数据到数据库**

## 最佳实践

### 1. 查询AI解读

```python
# 推荐方式：通过Paper关联查询
paper = session.query(Paper).filter_by(id=paper_id).first()
if paper.interpretation:
    content = paper.interpretation.interpretation
```

### 2. 生成TTS内容

```python
# 使用TTS服务中的清理函数
from app.services.content_generation.tts_generate import clean_markdown_for_tts

if paper.interpretation:
    tts_content = clean_markdown_for_tts(paper.interpretation.interpretation)
```

### 3. 检查数据完整性

```python
# 检查论文是否有AI解读
has_interpretation = paper.interpretation is not None

# 检查论文是否有TTS音频
has_tts = len(paper.tts_files) > 0
```

## 数据统计

截至最后更新：
- **总AI解读记录**: 3042条
- **Markdown格式**: 2848条 (93.6%)
- **结构化文本**: 194条 (6.4%)
- **平均长度**: 约1000字符
- **TTS音频文件**: 存储在`backend/data/tts/`

## 维护说明

### 格式统一

所有AI解读已统一为markdown格式，如需重新统一格式，可运行：

```bash
# 分析当前格式分布
python backend/process_ai_interpretations.py --analyze

# 转换JSON格式为markdown
python backend/process_ai_interpretations.py --convert --execute

# 修复剩余异常格式
python backend/fix_remaining_records.py --execute
```

### 数据迁移

如需从`PaperTranslation.ai_interpretation`迁移到`PaperInterpretation`：

```python
from app.models import PaperTranslation, PaperInterpretation

translations = session.query(PaperTranslation).filter(
    PaperTranslation.ai_interpretation.isnot(None)
).all()

for trans in translations:
    # 检查是否已存在
    existing = session.query(PaperInterpretation).filter_by(
        paper_id=trans.paper_id
    ).first()
    
    if not existing:
        interpretation = PaperInterpretation(
            paper_id=trans.paper_id,
            interpretation=trans.ai_interpretation,
            language="zh",
            model_name=trans.model_name
        )
        session.add(interpretation)

session.commit()
```

## 相关文件

- **模型定义**: `backend/app/models/paper.py`
- **TTS模型**: `backend/app/models/paper_tts.py`
- **AI解读服务**: `backend/app/services/ai_interpretation_unified.py`
- **TTS生成服务**: `backend/app/services/tts_generate.py`
- **格式处理脚本**: `backend/process_ai_interpretations.py`
- **格式修复脚本**: `backend/fix_remaining_records.py`
