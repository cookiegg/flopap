#!/usr/bin/env python3
import sys
from pathlib import Path
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from app.services.llm import get_deepseek_clients

def test_translation_parsing():
    print('=== 测试翻译解析 ===')
    
    # 测试有特殊字符的标题
    test_title = "${D}^{3}${ETOR}: ${D}$ebate-Enhanced Pseudo Labeling and Frequency-Aware Progressive ${D}$ebiasing for Weakly-Supervised Camouflaged Object ${D}$etection with Scribble Annotations"
    test_abstract = "Weakly-Supervised Camouflaged Object Detection (WSCOD) aims to locate and segment objects that are visually concealed within their surrounding scenes."
    
    prompt = f"""请将以下英文论文标题和摘要翻译成中文：

标题：{test_title}

摘要：{test_abstract}

请按以下格式返回：
标题：[中文标题]
摘要：[中文摘要]"""
    
    clients = get_deepseek_clients()
    client = clients[0]
    
    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        print("原始响应:")
        print(content)
        print("\n" + "="*50)
        
        # 测试解析逻辑
        lines = content.split('\n')
        title_zh = ""
        summary_zh = ""
        
        for line in lines:
            line = line.strip()
            print(f"处理行: '{line}'")
            if line.startswith('标题：'):
                title_zh = line[3:].strip()
                print(f"  -> 提取标题: '{title_zh}'")
            elif line.startswith('摘要：'):
                summary_zh = line[3:].strip()
                print(f"  -> 提取摘要: '{summary_zh}'")
        
        print(f"\n最终结果:")
        print(f"标题是否为空: {not title_zh}")
        print(f"摘要是否为空: {not summary_zh}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_translation_parsing()
