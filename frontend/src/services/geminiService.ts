
import { Insight } from "../types";

// NOTE: This service is fully mocked. No API calls.

export const translatePaper = async (title: string, abstract: string): Promise<{ translatedTitle: string; translatedAbstract: string }> => {
  // Simulate a very short network delay
  await new Promise(resolve => setTimeout(resolve, 300));

  return {
    translatedTitle: `[模拟翻译] ${title}`,
    translatedAbstract: `(模拟长文本翻译)\n\n${abstract}\n\n[附加说明]：此段落为模拟生成的翻译结果，旨在测试界面在展示长篇幅中文内容时的滚动交互体验。`
  };
};

export const generateInsights = async (abstract: string): Promise<Insight[]> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  
  return [
    {
      en: "Context: Testing long scrolling behavior in mobile interfaces.",
      zh: "背景与动机：为了验证移动端界面的滚动交互是否流畅，我们需要生成具有足够长度的测试数据。传统的短文本无法触发滚动条，因此无法测试卡片切换与内部滚动的冲突。"
    },
    {
      en: "Method: Hardcoded long strings in constants.",
      zh: "核心方法：我们在前端常数文件中硬编码了长段落文本，包括摘要、翻译和解读。通过 CSS 的 overscroll-behavior 属性，我们控制了滚动事件的冒泡行为，实现了内部滚动到底部后自动触发父容器翻页的效果。"
    },
    {
      en: "Impact: Seamless UX for reading papers.",
      zh: "结果与影响：这种设计极大地提升了用户体验。用户可以在不误触翻页的情况下阅读长文，而在阅读完毕后，只需稍加用力滑动即可切换到下一篇论文，完美模拟了原生应用的流畅感。"
    }
  ];
};

export const generatePaperVisualization = async (title: string): Promise<string> => {
    // Simulate a delay
    await new Promise(r => setTimeout(r, 2000));
    const encodedTitle = encodeURIComponent(title.substring(0, 50));
    return `https://pollinations.ai/p/${encodedTitle}?width=800&height=800&seed=42&model=flux`;
};
