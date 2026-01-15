"""
内容生成服务模块
包含AI解读、翻译、TTS、信息图表、可视化等内容生成服务

实际可用的函数:
- TTS: generate_single_tts, batch_generate_tts_async
- 翻译: translate_single_paper, batch_translate_papers  
- AI解读: generate_single_interpretation, batch_generate_interpretations
- 可视化: generate_visual_explanation, generate_visual_with_imagen
- 信息图表: generate_infographics_batch, generate_single_infographic

使用方式:
    from app.services.content_generation.tts_generate import batch_generate_tts_async
    from app.services.content_generation.translation_generate import translate_single_paper
    from app.services.content_generation.visualization_generate import generate_visual_explanation
"""

# 内容生成服务文件夹
# 所有服务通过直接导入使用，避免命名冲突
