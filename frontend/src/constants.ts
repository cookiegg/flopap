
export const ARXIV_CATEGORIES = [
  { id: 'cs.AI', name: 'Artificial Intelligence' },
  { id: 'cs.CV', name: 'Computer Vision' },
  { id: 'cs.LG', name: 'Machine Learning' },
  { id: 'cs.CL', name: 'Computation and Language' },
  { id: 'cs.RO', name: 'Robotics' },
  { id: 'cs.CR', name: 'Cryptography and Security' },
  { id: 'cs.SE', name: 'Software Engineering' },
  { id: 'physics.comp-ph', name: 'Computational Physics' },
  { id: 'math.OC', name: 'Optimization and Control' },
  { id: 'q-bio.NC', name: 'Neurons and Cognition' },
  { id: 'stat.ML', name: 'Machine Learning (Stat)' },
];

export const UI_STRINGS = {
  en: {
    dailyUpdates: 'Daily Updates',
    conferences: 'Conferences',
    latestResearch: 'Latest Research',
    settings: 'Settings & Menu',
    language: 'Language',
    theme: 'Theme',
    darkMode: 'Dark Mode',
    lightMode: 'Light Mode',
    generating: 'Generating...',
    published: 'Published',
    translatedBy: 'Translated by AI',
    aiInsights: 'AI Core Insights',
    enHighlights: 'English Highlights',
    visualExp: 'AI Visual Explanation',
    generateVis: 'Generate Visualization',
    startGen: 'Start Generation',
    highCost: 'High Cost Operation',
    estCost: 'Estimated Cost',
    estTime: 'Estimated Time',
    cancel: 'Cancel',
    confirm: 'Confirm',
    retry: 'Retry / Refresh',
    noPapers: 'No papers found.',
    like: 'Like',
    save: 'Save',
    web: 'Web',
    share: 'Share',
    hide: 'Hide',
    back: 'Back',
    home: 'Home',
    profile: 'Profile',
    logout: 'Logout',
    editProfile: 'Edit Preferences',
    myTopics: 'My Topics',
    myKeywords: 'My Keywords',
    saveChanges: 'Save Changes',
    insightLabels: {
      context: 'Context',
      method: 'Method',
      impact: 'Impact'
    },
    // Profile Specific
    guestUser: 'Guest User',
    communityUser: 'Community User',
    cloudUser: 'Cloud User',
    welcome: 'Welcome to FloPap',
    welcomeBack: 'Welcome back to FloPap',
    prefsTab: 'Preferences',
    likesTab: 'Likes',
    savedTab: 'Saved',
    customizeFeed: 'Customize Feed',
    addKeywordPlaceholder: 'Add keyword...',
    yourTopics: 'Your Topics',
    yourKeywords: 'Your Keywords',
    noneSelected: 'None selected',
    noneSet: 'None set',
    nothingHere: 'Nothing here yet. Go explore!',
    loading: 'Loading papers...',
    // Hide Confirmation
    hideConfirmTitle: 'Hide Paper?',
    hideConfirmText: 'This will remove this paper from your feed permanently. This action cannot be undone.',
    // Login Screen
    loginSlogan: 'Swipe through the latest research.\nEffortless. Intelligent. Visual.',
    loginGoogle: 'Continue with Google',
    loginPhone: 'Phone',
    loginGoogleBtn: 'Google',
    enterPhone: 'Phone Number',
    enterCode: 'Verification Code',
    sendCode: 'Send Code',
    loginRegister: 'Login / Register',
    verifying: 'Verifying...',
    connecting: 'Connecting...',
    loginFailed: 'Login failed, please try again',
    validPhoneReq: 'Please enter a valid phone number',
    enterBothReq: 'Please enter phone number and code',
    privacy: 'Privacy Policy',
    terms: 'Terms of Service',
    // AI Settings
    aiSettingsTitle: 'API Key Management',
    addKey: 'Add Key',
    securityNote: 'Security Note',
    securityText: 'API keys are encrypted and stored locally. They are only used to generate content for you.',
    serviceSelector: 'Select Service',
    keyInputPlaceholder: 'Enter API Key',
    validateKey: 'Validate Key',
    saveKey: 'Save Key',
    validating: 'Validating...',
    saving: 'Saving...',
    keyValid: 'Key is valid',
    keyInvalid: 'Verification failed',
    usage: 'Usage',
    lastUsed: 'Last used',
    neverUsed: 'Never used',
    deleteKeyConfirm: 'Are you sure you want to delete this API Key?',
    selectServiceReq: 'Please select a service',
    // Recommendation Settings
    recSettingsTitle: 'Recommendation Settings',
    recRatio: 'Recommendation Ratio',
    arxivRatio: 'arXiv Ratio',
    confRatio: 'Conference Ratio',
    poolSize: 'Pool Size',
    autoGen: 'Auto Generation',
    enableAutoGen: 'Enable Auto Generation',
    autoGenDesc: 'Automatically generate translations and insights for recommended papers',
    prefModels: 'Preferred Models',
    prefModelsDesc: 'Selected models will be prioritized for content generation',
    saveSettings: 'Save Settings',
    settingsSaved: 'Settings Saved',
    // Landing Page
    startReading: 'Start Reading',
    downloadApp: 'Download App',
    features: 'Features',
    feature1Title: 'AI Insights',
    feature1Desc: 'Get core insights in seconds',
    feature2Title: 'Bilingual',
    feature2Desc: 'One-click translation',
    feature3Title: 'Vertical Scroll',
    feature3Desc: 'TikTok-style experience',
    scanToDownload: 'Scan to Download',
    webVersion: 'Web Version',
    mobileVersion: 'Mobile App'
  },
  zh: {
    dailyUpdates: '每日更新',
    conferences: '顶级会议',
    latestResearch: '最新研究',
    settings: '设置与菜单',
    language: '语言设置',
    theme: '主题设置',
    darkMode: '深色模式',
    lightMode: '浅色模式',
    generating: '生成中...',
    published: '发布于',
    translatedBy: 'AI 翻译',
    aiInsights: 'AI 核心解读',
    enHighlights: '英文要点',
    visualExp: 'AI 可视化讲解',
    generateVis: '生成讲解图',
    startGen: '开始生成',
    highCost: '高成本操作',
    estCost: '预估成本',
    estTime: '预估时间',
    cancel: '取消',
    confirm: '确认',
    retry: '重试 / 刷新',
    noPapers: '暂无论文',
    like: '点赞',
    save: '收藏',
    web: '网页',
    share: '分享',
    hide: '不感兴趣',
    back: '返回',
    home: '首页',
    profile: '个人主页',
    logout: '退出登录',
    editProfile: '编辑偏好',
    myTopics: '关注领域',
    myKeywords: '关键词',
    saveChanges: '保存修改',
    insightLabels: {
      context: '背景与动机',
      method: '核心方法',
      impact: '结果与影响'
    },
    // Profile Specific
    guestUser: '访客用户',
    communityUser: '社区用户',
    cloudUser: '云服务用户',
    welcome: '欢迎来到 FloPap',
    welcomeBack: '欢迎回到 FloPap',
    prefsTab: '偏好设置',
    likesTab: '喜欢',
    savedTab: '收藏',
    customizeFeed: '自定义推荐',
    addKeywordPlaceholder: '添加关键词...',
    yourTopics: '已选领域',
    yourKeywords: '关键词',
    noneSelected: '未选择',
    noneSet: '未设置',
    nothingHere: '暂无内容，快去探索吧！',
    loading: '正在加载...',
    // Hide Confirmation
    hideConfirmTitle: '不再显示此论文？',
    hideConfirmText: '确认后将从推荐列表中移除此论文，该操作不可恢复。',
    // Login Screen
    loginSlogan: '刷论文，从未如此轻松。\n智能解读，一眼即懂。',
    loginGoogle: 'Google 账号登录',
    loginPhone: '手机登录',
    loginGoogleBtn: 'Google',
    enterPhone: '手机号码',
    enterCode: '验证码',
    sendCode: '发送验证码',
    loginRegister: '登录 / 注册',
    verifying: '验证中...',
    connecting: '连接中...',
    loginFailed: '登录失败，请重试',
    validPhoneReq: '请输入有效的手机号码',
    enterBothReq: '请输入手机号和验证码',
    privacy: '隐私政策',
    terms: '服务条款',
    // AI Settings
    aiSettingsTitle: 'API 密钥管理',
    addKey: '添加密钥',
    securityNote: '安全提醒',
    securityText: 'API密钥将被加密存储，仅用于为您生成内容。请确保使用官方渠道获取的密钥。',
    serviceSelector: '选择服务',
    keyInputPlaceholder: '请输入 API 密钥',
    validateKey: '验证密钥',
    saveKey: '保存密钥',
    validating: '验证中...',
    saving: '保存中...',
    keyValid: '密钥有效',
    keyInvalid: '验证失败',
    usage: '使用情况',
    lastUsed: '上次使用',
    neverUsed: '从未使用',
    deleteKeyConfirm: '确定要删除此 API 密钥吗？',
    selectServiceReq: '请选择服务',
    // Recommendation Settings
    recSettingsTitle: '推荐设置',
    recRatio: '推荐比例',
    arxivRatio: 'arXiv 比例',
    confRatio: '会议论文比例',
    poolSize: '推荐池大小',
    autoGen: '自动生成',
    enableAutoGen: '启用自动生成',
    autoGenDesc: '为推荐论文自动生成翻译和解读内容',
    prefModels: '偏好模型',
    prefModelsDesc: '选中的模型将优先用于内容生成',
    saveSettings: '保存设置',
    settingsSaved: '设置已保存',
    // Landing Page
    startReading: '开始阅读',
    downloadApp: '下载 APP',
    features: '核心功能',
    feature1Title: 'AI 深度解读',
    feature1Desc: '秒懂核心内容',
    feature2Title: '中英双语',
    feature2Desc: '无障碍阅读体验',
    feature3Title: '沉浸式体验',
    feature3Desc: '像刷视频一样刷论文',
    scanToDownload: '扫码下载 App',
    webVersion: 'Web 网页版',
    mobileVersion: '移动客户端'
  }
};

const LONG_ABSTRACT = `Recent advancements in Large Language Models (LLMs) have demonstrated remarkable capabilities in reasoning, coding, and general natural language understanding. However, as these models grow in size, their deployment becomes increasingly challenging due to memory and latency constraints. In this paper, we introduce "Infinite-Context-Lite," a novel architecture designed to handle effectively infinite context lengths while maintaining the inference speed of small models.

We begin by analyzing the bottleneck of Key-Value (KV) cache in standard Transformer architectures. Traditionally, the memory usage grows linearly with sequence length, making long-context inference prohibitively expensive. Our proposed method employs a dynamic compression mechanism that selectively retains only the most semantic-rich tokens in the memory, discarding redundant information without sacrificing retrieval accuracy. 

Furthermore, we introduce a hierarchical memory retrieval system inspired by biological short-term and long-term memory processes. This allows the model to "recall" information from millions of tokens ago with O(log N) complexity. We rigorously evaluate our model on the LongBench benchmark and several proprietary datasets containing legal contracts and full-length novels. 

Our results show that Infinite-Context-Lite achieves state-of-the-art performance on context retrieval tasks exceeding 1M tokens, while running on a single A100 GPU. We also conduct extensive ablation studies to understand the contribution of each component. Finally, we discuss the ethical implications of infinite-context models and propose a framework for safe deployment. This work paves the way for truly personalized AI assistants that can remember user interactions over years.

(Extended Paragraph for Scrolling Test)
To further validate the scalability of our approach, we conducted stress tests involving concurrent requests simulating a real-world production environment. The results indicate that Infinite-Context-Lite maintains a stable throughput even under heavy load, outperforming existing sparse-attention baselines by a margin of 40%. The adaptive token pruning strategy not only reduces memory footprint but also acts as a noise filter, improving the model's ability to stay on topic during extended generation sessions. We believe this architectural shift represents a significant step towards democratizing access to long-context AI capabilities.`;

const LONG_ZH_ABSTRACT = `近年来，大型语言模型（LLM）在推理、编程和通用自然语言理解方面展现出了惊人的能力。然而，随着模型规模的不断扩大，受限于显存和延迟，其部署变得愈发困难。在本文中，我们推出了“Infinite-Context-Lite”，这是一种全新的架构，旨在有效处理无限上下文长度，同时保持小型模型的推理速度。

我们首先分析了标准 Transformer 架构中键值（KV）缓存的瓶颈。传统上，内存使用量随序列长度线性增长，这使得长上下文推理极其昂贵。我们提出的方法采用了一种动态压缩机制，仅在内存中保留语义最丰富的 token，在不牺牲检索准确性的情况下丢弃冗余信息。

此外，我们引入了一种受生物短时记忆和长时记忆过程启发的各种分层内存检索系统。这使得模型能够以 O(log N) 的复杂度“回想”起数百万个 token 之前的信息。我们在 LongBench 基准测试以及包含法律合同和长篇小说的几个专有数据集上对我们的模型进行了严格评估。

结果表明，Infinite-Context-Lite 在超过 100 万 token 的上下文检索任务上达到了最先进的性能，且仅需单张 A100 GPU 即可运行。我们还进行了广泛的消融研究，以理解每个组件的贡献。最后，我们讨论了无限上下文模型的伦理影响，并提出了安全部署的框架。这项工作为能够记住用户数年交互的真正个性化 AI 助手铺平了道路。

(用于滚动测试的扩展段落)
为了进一步验证我们方法的可扩展性，我们进行了涉及模拟真实生产环境的并发请求的压力测试。结果表明，即使在重负载下，Infinite-Context-Lite 也能保持稳定的吞吐量，比现有的稀疏注意力基线高出 40%。自适应 token 剪枝策略不仅减少了内存占用，还充当了噪声过滤器，提高了模型在长时间生成会话中保持主题的能力。我们相信，这种架构转变代表了向大众化长上下文 AI 能力迈出的重要一步。`;

export const MOCK_PAPERS_DATA = [
  {
    id: '2401.LONG',
    title: 'Infinite-Context-Lite: Efficient Long-Context Inference for Large Language Models',
    abstract: LONG_ABSTRACT,
    authors: ['Alice Researcher', 'Bob Scientist', 'Charlie Engineer'],
    categories: ['cs.CL', 'cs.AI'],
    publishedDate: '2024-05-20',
    translatedTitle: 'Infinite-Context-Lite：大型语言模型的高效长上下文推理',
    translatedAbstract: LONG_ZH_ABSTRACT,
    visualizationUrl: 'https://pollinations.ai/p/Infinite-Context-Lite?width=800&height=800&seed=42&model=flux',
    aiInsights: [
      {
        en: "Context: LLMs struggle with memory costs for long texts.",
        zh: "背景与动机：大型语言模型在处理长文本时面临巨大的显存开销，这限制了它们处理书籍或长历史记录的能力。"
      },
      {
        en: "Method: Hierarchical memory retrieval with O(log N) complexity.",
        zh: "核心方法：提出了一种分层记忆检索系统，模仿人类的短期和长期记忆。它能智能压缩不重要的信息，只保留关键语义，从而将检索复杂度降低到对数级。"
      },
      {
        en: "Impact: Runs 1M context on single GPU.",
        zh: "结果与影响：实现了在单张显卡上处理百万字上下文的能力，这让个人 AI 助手能够拥有“无限记忆”，能够记住用户几个月前的对话细节。"
      }
    ]
  },
];

export const generateMockPapers = (count: number): any[] => {
  const papers = [];
  for (let i = 0; i < count; i++) {
    const template = MOCK_PAPERS_DATA[i % MOCK_PAPERS_DATA.length];
    const uniqueSuffix = Math.random().toString(36).substr(2, 5);
    papers.push({
      ...template,
      id: `${template.id}-${uniqueSuffix}`,
      title: `${template.title} (Vol. ${uniqueSuffix.toUpperCase()})`,
    });
  }
  return papers;
};
