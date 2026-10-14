export interface Opportunity {
  id: string;
  name: string;
  category: string;
  score: number;
  priority: '高' | '中' | '低';
  status: '研判中' | '新发现' | '持续跟踪' | '已忽略' | '已归档';
  evidenceCount: number;
  marketSize: string;
  growthRate: string;
  competition: string;
  barrier: string;
  owner: string;
  ownerRole: string;
  updatedAt: string;
  summary: string;
  drivers: string[];
  keyRisks: string[];
  timeline: Array<{
    source: string;
    title: string;
    time: string;
    reliability: string;
  }>;
  suggestedSteps: Array<{
    title: string;
    desc: string;
  }>;
}

export interface IntelligenceItem {
  id: string;
  title: string;
  source: string;
  sourceType: '权威来源' | '行业媒体' | '官方博客' | '开源社区' | '学术论文';
  publishedAt: string;
  author: string;
  summary: string;
  fullText: string;
  score: number;
  reliability: '高置信度' | '中置信度' | '低置信度';
  priority: '高相关' | '中相关' | '低相关';
  tags: string[];
  entities: Array<{ name: string; type: '公司' | '产品' | '技术' | '人物' }>;
  keySignals: string[];
  isBookmarked?: boolean;
}

export interface ResearchWorkflowItem {
  id: string;
  title: string;
  opportunityId: string;
  opportunityName: string;
  progress: number;
  stage: '资料收集' | '假设验证' | '初步分析' | '撰写报告' | '已完成';
  owner: string;
  ownerAvatar: string;
  updatedAt: string;
  keyConclusion?: string;
  deliverables: string[];
  logs: Array<{
    timestamp: string;
    stage: string;
    message: string;
    status: 'success' | 'running' | 'warning' | 'error';
  }>;
}

export interface MonitoringPlan {
  id: string;
  name: string;
  keywords?: string[];
  scope?: string;
  healthScore?: number;
  totalRuns?: number;
  target?: string;
  frequency: string;
  sourceCount: number;
  sourcesCount?: number;
  signalCount: number;
  signalsCount?: number;
  alertCount?: number;
  nextRun?: string;
  status: '运行中' | '已暂停' | '草稿' | '异常';
  updatedAt: string;
}

export interface RunHistoryItem {
  id: string;
  planId: string;
  planName: string;
  triggerType: '定时调度' | '手动触发' | 'API调用' | '自动调度' | '定时触发';
  startTime: string;
  duration: string;
  status: '成功' | '部分失败' | '运行中' | '失败' | '重试';
  collectedCount: number;
  newSignals: number;
  newSignalsCount?: number;
  sourcesCount?: number;
  errorCount?: number;
  dedupedCount: number;
  failedSources: number;
  stages?: Array<{
    name: string;
    status: 'success' | 'failed' | 'running' | 'pending';
    duration: string;
    count: number;
  }>;
}

export interface AnalysisQueueTask {
  id: string;
  type?: string;
  target?: string;
  targetName?: string;
  taskType?: string;
  runId?: string;
  worker?: string;
  status: '处理中' | '待处理' | '重试中' | '失败' | '已完成';
  priority: 'P0' | 'P1' | 'P2' | '高' | '中' | '低';
  duration?: string;
  waitingTime?: string;
  retryCount?: number;
  estimatedFinish?: string;
  createdAt?: string;
  errorReason?: string;
}

export interface AlertItem {
  id: string;
  title: string;
  type?: string;
  severity: '高' | '中' | '低' | '严重';
  source: string;
  target?: string;
  owner?: string;
  time: string;
  status: '未读' | '处理中' | '已解决' | '已忽略';
  relatedRunId?: string;
  relatedOpportunityId?: string;
  detail?: string;
  suggestedAction?: string;
}

export interface Member {
  id: string;
  name: string;
  email: string;
  role: string;
  opportunitiesCount: number;
  researchCount: number;
  lastActive: string;
  joinedAt?: string;
  status: '正常' | '已邀请' | '已停用' | '暂停';
  avatar: string;
}

export interface IntegrationItem {
  id: string;
  name: string;
  category: 'IM 通知' | '项目协作' | '代码与数据' | '自定义 Webhook';
  status: 'connected' | 'error' | 'disconnected';
  desc: string;
  icon: string;
  lastSync: string;
  errorDetail?: string;
}

// ----------------------------------------------------
// Global Constant Mock Dataset
// ----------------------------------------------------

export const MOCK_OPPORTUNITIES: Opportunity[] = [
  {
    id: 'OPP-20260819-021',
    name: '企业级AI知识管理平台',
    category: '企业服务 / AI',
    score: 85,
    priority: '高',
    status: '研判中',
    evidenceCount: 32,
    marketSize: '320 亿',
    growthRate: '年增长 28%',
    competition: '中等 (主要竞品 8 家)',
    barrier: '中等 (技术 + 数据)',
    owner: '张天宇',
    ownerRole: '高级分析师',
    updatedAt: '15分钟前',
    summary: '企业知识管理需求持续增长，大模型能力让文档理解、企业检索、智能问答和知识沉淀出现新的产品窗口。当前客户付费意愿正在上升，竞争格局尚未完全稳定。',
    drivers: [
      '企业数字化与知识资产治理投入增加',
      '大模型推理成本下降，私有化部署成熟',
      '知识检索与工作流自动化需求增强',
      '头部客户开始形成规模化采购'
    ],
    keyRisks: [
      '数据安全合规政策收紧导致交付周期延长',
      '通用大模型底座厂商向下侵蚀应用层',
      '企业遗留异构数据清洗成本超出预期'
    ],
    timeline: [
      { source: 'TechCrunch', title: '企业AI助手进入采购周期', time: '15分钟前', reliability: '高可信' },
      { source: 'Gartner', title: '知识管理市场上调增长预期', time: '2小时前', reliability: '行业报告' },
      { source: '客户访谈', title: '42%企业计划增加预算', time: '昨天', reliability: '用户调研' },
      { source: '竞品发布', title: '私有化部署版本上线', time: '3天前', reliability: '产品动态' }
    ],
    suggestedSteps: [
      { title: '深入市场研究', desc: '验证市场空间、竞争与价格带' },
      { title: '客户需求验证', desc: '访谈目标客户并验证购买意愿' },
      { title: '建立持续监控', desc: '跟踪产品发布、融资和招聘信号' }
    ]
  },
  {
    id: 'OPP-20260819-022',
    name: '可持续航空燃料 (SAF) 供应链优化',
    category: '新能源 / 环保',
    score: 72,
    priority: '中',
    status: '持续跟踪',
    evidenceCount: 18,
    marketSize: '540 亿',
    growthRate: '年增长 42%',
    competition: '较低 (技术门槛极高)',
    barrier: '极高 (原料资质与炼化工艺)',
    owner: '王明',
    ownerRole: '分析师',
    updatedAt: '1小时前',
    summary: '随着国际民航组织及欧盟对航空碳排放法规收紧，可持续航空燃料需求呈爆发性增长，原料收集与供应链追踪存在巨大平台级机会。',
    drivers: ['欧盟法规强制掺混比例提升', '航空公司碳中和承诺兑现压力', '生物质原料溯源技术突破'],
    keyRisks: ['原料供应季节性波动', '传统化石燃油价格下行压制替代意愿'],
    timeline: [
      { source: 'Reuters', title: '欧盟通过新一代航空燃油指令', time: '1小时前', reliability: '权威政策' },
      { source: 'IATA', title: '2026 全球 SAF 采购意向统计', time: '3天前', reliability: '行业协会' }
    ],
    suggestedSteps: [
      { title: '原料基地调研', desc: '评估废弃油脂收集网络集中度' },
      { title: '政策补贴测算', desc: '分析欧盟与北美税收抵免机制' }
    ]
  },
  {
    id: 'OPP-20260819-023',
    name: '边缘计算在工业物联网中的应用',
    category: '工业互联网',
    score: 68,
    priority: '高',
    status: '研判中',
    evidenceCount: 24,
    marketSize: '180 亿',
    growthRate: '年增长 22%',
    competition: '中等',
    barrier: '高 (软硬协同与协议适配)',
    owner: '张天宇',
    ownerRole: '高级分析师',
    updatedAt: '2小时前',
    summary: '高精工控现场对超低延迟和本地推理要求提升，具备轻量级大模型加速能力的工控边缘一体机正在进入产线测试。',
    drivers: ['工业视觉质检算力本地化需求', '产线通信协议异构整合难度下降'],
    keyRisks: ['工业客户选型周期长', '硬件毛利率受上游芯片波动影响'],
    timeline: [
      { source: '工信部', title: '推动人形机器人与工业现场创新发展', time: '2小时前', reliability: '政策法规' }
    ],
    suggestedSteps: [
      { title: '典型灯塔工厂调研', desc: '考察 3 家离散制造工厂边缘节点部署方案' }
    ]
  },
  {
    id: 'OPP-20260819-024',
    name: '基因编辑疗法商业化加速',
    category: '生物科技',
    score: 65,
    priority: '中',
    status: '新发现',
    evidenceCount: 15,
    marketSize: '120 亿',
    growthRate: '年增长 35%',
    competition: '中等',
    barrier: '极高 (专利与临床审批)',
    owner: '李强',
    ownerRole: '分析师',
    updatedAt: '3小时前',
    summary: '针对罕见病和血液疾病的多款体内基因编辑疗法在海外获批进入商业化快速通道，国内申报节奏明显加快。',
    drivers: ['CRISPR 递送系统脱靶率持续降低', 'FDA 加速审评通道支持'],
    keyRisks: ['单疗程定价过高导致支付方覆盖困难'],
    timeline: [
      { source: 'BioPharma Dive', title: '辉瑞公布最新临床进展', time: '3小时前', reliability: '行业快讯' }
    ],
    suggestedSteps: [{ title: '医保支付准入评估', desc: '分析多国商保与医保谈判策略' }]
  },
  {
    id: 'OPP-20260819-025',
    name: '新型固态电池材料突破',
    category: '新能源',
    score: 63,
    priority: '中',
    status: '研判中',
    evidenceCount: 17,
    marketSize: '890 亿',
    growthRate: '年增长 45%',
    competition: '激烈',
    barrier: '极高 (固态电解质离子电导率)',
    owner: '王明',
    ownerRole: '分析师',
    updatedAt: '4小时前',
    summary: '硫化物与聚合物复合固态电解质量产成本下探，车规级搭载时间表提前至 2026 年底。',
    drivers: ['新能源汽车长续航与超高安全诉求', '低空飞行器对能量密度极端要求'],
    keyRisks: ['干法电极工艺良品率爬坡不及预期'],
    timeline: [
      { source: 'Electrek', title: '固态电池产线进度超预期', time: '2小时前', reliability: '技术突破' }
    ],
    suggestedSteps: [{ title: '头部电池厂专利穿透', desc: '检索近期公布的 14 项关键电解质专利' }]
  },
  {
    id: 'OPP-20260819-026',
    name: '人形机器人核心零部件国产化',
    category: '机器人 / 智能制造',
    score: 61,
    priority: '中',
    status: '新发现',
    evidenceCount: 12,
    marketSize: '240 亿',
    growthRate: '年增长 58%',
    competition: '中等',
    barrier: '高 (高功率密度关节与减速器)',
    owner: '李强',
    ownerRole: '分析师',
    updatedAt: '5小时前',
    summary: '灵巧手传感器与微型行星滚柱丝杠供应商陆续进入量产送样阶段，整机 BOM 成本预期下降 30% 以上。',
    drivers: ['特斯拉与国内主机厂供应链定点释放', '灵巧手多维触觉阵列国产替代成熟'],
    keyRisks: ['整机场景实际出货量短期低于乐观预期'],
    timeline: [{ source: '财新网', title: '人形机器人供应链调研', time: '5小时前', reliability: '深度研报' }],
    suggestedSteps: [{ title: '供应链降本测算', desc: '拆解六维力传感器与丝杠成本结构' }]
  },
  {
    id: 'OPP-20260819-027',
    name: '空间计算资源市场化生态',
    category: '云计算 / AI',
    score: 58,
    priority: '低',
    status: '持续跟踪',
    evidenceCount: 9,
    marketSize: '95 亿',
    growthRate: '年增长 18%',
    competition: '分散',
    barrier: '中等',
    owner: '张天宇',
    ownerRole: '高级分析师',
    updatedAt: '6小时前',
    summary: '去中心化闲置算力聚合平台接入门槛降低，小微开发者针对轻量微调任务的采购占比明显提升。',
    drivers: ['端侧模型蒸馏需求爆发', '分布式算力调度网络延迟优化'],
    keyRisks: ['算力提供方节点稳定性与数据泄露风险'],
    timeline: [{ source: 'VentureBeat', title: '分布式算力网络最新投融资', time: '6小时前', reliability: '创投动态' }],
    suggestedSteps: [{ title: '算力节点可用率测试', desc: '监测 5 家去中心化网络实际吞吐与丢包' }]
  }
];

export const MOCK_INTELLIGENCE: IntelligenceItem[] = [
  {
    id: 'INT-20260819-01842',
    title: 'OpenAI 发布企业级 AI 助手新功能，支持私有化部署',
    source: '路透社 · Reuters',
    sourceType: '权威来源',
    publishedAt: '2025-05-13 09:30',
    author: 'OpenAI Product Team / Reuters',
    score: 86,
    reliability: '高置信度',
    priority: '高相关',
    tags: ['人工智能', '大模型', '私有化部署', '企业服务', '数据安全'],
    entities: [
      { name: 'OpenAI', type: '公司' },
      { name: 'ChatGPT Enterprise', type: '产品' },
      { name: '私有化部署', type: '技术' },
      { name: 'Microsoft 365', type: '产品' },
      { name: 'Google Workspace', type: '产品' }
    ],
    summary: 'OpenAI 在官网发布针对企业客户的多项 ChatGPT Enterprise 新功能，包括私有化部署选项、数据隔离增强、企业级管理控制台升级以及与主流企业应用深度集成。新功能旨在帮助大型组织在保障数据安全与合规的前提下，规模化部署生成式 AI，提升员工生产力并优化业务流程。',
    fullText: `2025 年 5 月 13 日，OpenAI 在其官方博客中宣布，为 ChatGPT Enterprise 客户推出一系列面向企业级组织的高级增强功能与部署选项，进一步满足大型组织在安全性、合规性与可扩展性方面的需求。

核心更新包括：提供私有化部署选项（Private Deployment），支持客户在自有云或本地数据中心运行模型；默认启用数据隔离与零保留策略，确保业务数据不用于模型训练；升级企业级管理控制台，新增精细化权限管理、使用分析与审计日志；并支持与 Microsoft 365、Google Workspace、Slack、Salesforce 等主流应用的深度集成。

OpenAI 表示，这些能力将帮助企业在更严格的安全与合规要求下，规模化部署生成式 AI，赋能知识管理、内容创作、客户支持、数据分析等多个核心场景，从而推动组织效率与创新的提升。`,
    keySignals: [
      '支持实时语音对话，延迟低至 232ms',
      '视觉理解能力提升，支持图片和视频输入',
      '在 MMLU、GPQA 等基准测试中领先',
      '将逐步向 ChatGPT Plus 用户开放'
    ],
    isBookmarked: true
  },
  {
    id: 'INT-20260819-01843',
    title: '国家发改委：加快布局算力基础设施，支持智算中心建设',
    source: '36氪 · 36Kr',
    sourceType: '行业媒体',
    publishedAt: '32 分钟前',
    author: '36Kr 宏观快讯',
    score: 78,
    reliability: '高置信度',
    priority: '高相关',
    tags: ['政策法规', '算力基础设施', '智算中心', '新基建'],
    entities: [
      { name: '国家发改委', type: '公司' },
      { name: '智算中心', type: '技术' }
    ],
    summary: '国家发展改革委印发《算力基础设施高质量发展行动方案》，提出到 2026 年底全国算力总规模达到 300 EFLOPS 以上，智能算力占比达到 35%。',
    fullText: '发改委强调加快跨区域算力调度网络建设，降低算力使用成本，优先保障国家战略性人工智能重点研发攻关与产业赋能需求。',
    keySignals: ['智能算力占比目标提升至 35%', '西部绿色电力与算力协同示范工程落地']
  },
  {
    id: 'INT-20260819-01844',
    title: 'Anthropic 完成 60 亿美元融资，估值达 180 亿美元',
    source: 'TechCrunch',
    sourceType: '权威来源',
    publishedAt: '1 小时前',
    author: 'TechCrunch Silicon Valley',
    score: 82,
    reliability: '高置信度',
    priority: '高相关',
    tags: ['投融资', '大模型', 'Anthropic', 'Claude'],
    entities: [
      { name: 'Anthropic', type: '公司' },
      { name: 'Claude 3.5', type: '产品' }
    ],
    summary: 'Anthropic 宣布完成新一轮 60 亿美元融资，由 Lightspeed 领投，谷歌与亚马逊跟投，资金将主要用于下一代前沿大模型 Claude 4 的训练集群建设。',
    fullText: 'Anthropic 表示新资金将加速多模态企业级安全模型的迭代，并在全球范围内扩展直销与生态合作团队。',
    keySignals: ['估值跃升至 180 亿美元', '企业级订阅客户数单季度增长 140%']
  },
  {
    id: 'INT-20260819-01845',
    title: '工信部：推动人形机器人创新发展，突破关键核心技术',
    source: '财新网',
    sourceType: '权威来源',
    publishedAt: '2 小时前',
    author: '财新产业深度',
    score: 74,
    reliability: '高置信度',
    priority: '中相关',
    tags: ['政策法规', '机器人', '智能制造'],
    entities: [
      { name: '工信部', type: '公司' },
      { name: '人形机器人', type: '技术' }
    ],
    summary: '工信部印发《人形机器人创新发展指导意见》，提出到 2027 年实现核心部件自主可控，构建完善的产业生态体系。',
    fullText: '意见明确支持旋转执行器、高精度传感器及全身运动控制算法的联合攻关，设立首台套应用奖励机制。',
    keySignals: ['2027 年实现核心部件自主可控', '支持特种应用场景规模化试用']
  },
  {
    id: 'INT-20260819-01846',
    title: 'Meta 开源 Llama 3 模版，性能显著提升',
    source: 'GitHub',
    sourceType: '开源社区',
    publishedAt: '3 小时前',
    author: 'Meta AI',
    score: 81,
    reliability: '高置信度',
    priority: '高相关',
    tags: ['大模型', '开源', 'Meta', 'Llama 3'],
    entities: [
      { name: 'Meta', type: '公司' },
      { name: 'Llama 3', type: '产品' }
    ],
    summary: 'Meta 发布 Llama 3 系列模型，包括 8B 和 70B 两个版本，在多项基准测试中超越同尺寸闭源模型，并更新了更宽松的商业化许可协议。',
    fullText: 'Llama 3 在代码生成、数学推理及多语言对话方面表现突出，社区在 24 小时内适配了超过 50 款常用量化微调工具。',
    keySignals: ['开放 8k 上下文窗口', '全面支持本地轻量部署']
  },
  {
    id: 'INT-20260819-01847',
    title: '英伟达发布 Blackwell 架构芯片，算力提升 4 倍',
    source: '证券时报',
    sourceType: '权威来源',
    publishedAt: '4 小时前',
    author: '证券时报半导体专栏',
    score: 76,
    reliability: '高置信度',
    priority: '中相关',
    tags: ['芯片', '硬件', '英伟达', '算力'],
    entities: [
      { name: '英伟达', type: '公司' },
      { name: 'Blackwell B200', type: '产品' }
    ],
    summary: '英伟达在 GTC 大会上发布 Blackwell 架构的 B200 芯片，采用台积电 4NP 工艺，在 FP4 精度下提供高达 20 PFLOPS 的 AI 推理算力。',
    fullText: '新一代 NVLink 交换机支持 576 颗 GPU 高速互联，单集群通信带宽提升至 1.8 TB/s，极大缩短万亿参数模型训练时间。',
    keySignals: ['大模型推理能耗降低 25 倍', '第四季度开启首批云厂商交付']
  }
];

export const MOCK_RESEARCH_WORKFLOWS: ResearchWorkflowItem[] = [
  {
    id: 'RES-20260819-0011',
    title: '企业级AI知识管理平台商业可行性研究',
    opportunityId: 'OPP-20260819-021',
    opportunityName: '企业级AI知识管理平台',
    progress: 75,
    stage: '资料收集',
    owner: '张天宇',
    ownerAvatar: '张',
    updatedAt: '10分钟前',
    keyConclusion: '企业知识管理具备强付费意愿与极高粘性，私有化部署配合端侧大模型是打破客户合规顾虑的最优切入点。',
    deliverables: ['行业竞品功能矩阵', '20家企业客户采购意向清单', '私有化部署架构蓝图', '3年财务预测模型'],
    logs: [
      { timestamp: '14:20', stage: '资料收集', message: '完成 18 篇行业白皮书与技术报告解析', status: 'success' },
      { timestamp: '11:05', stage: '假设验证', message: '完成 5 家金融机构 IT 负责人访谈', status: 'success' },
      { timestamp: '09:30', stage: '初步分析', message: '生成初步竞争格局与价格带对比', status: 'success' }
    ]
  },
  {
    id: 'RES-20260819-0012',
    title: '可持续航空燃料 (SAF) 市场与政策分析',
    opportunityId: 'OPP-20260819-022',
    opportunityName: '可持续航空燃料 (SAF) 供应链优化',
    progress: 60,
    stage: '假设验证',
    owner: '王明',
    ownerAvatar: '王',
    updatedAt: '1小时前',
    deliverables: ['欧美政策补贴对比表', '全球原料产地分布拓扑'],
    logs: [{ timestamp: '昨天', stage: '资料收集', message: '抓取 IATA 最新航线减排规划', status: 'success' }]
  },
  {
    id: 'RES-20260819-0013',
    title: '工业物联网边缘计算商业路径研究',
    opportunityId: 'OPP-20260819-023',
    opportunityName: '边缘计算在工业物联网中的应用',
    progress: 40,
    stage: '初步分析',
    owner: '张天宇',
    ownerAvatar: '张',
    updatedAt: '2小时前',
    deliverables: ['工控协议适配成本评估'],
    logs: [{ timestamp: '2小时前', stage: '资料收集', message: '整理 12 款主流工控机硬件配置', status: 'success' }]
  },
  {
    id: 'RES-20260819-0014',
    title: '基因编辑疗法竞争格局与专利图谱',
    opportunityId: 'OPP-20260819-024',
    opportunityName: '基因编辑疗法商业化加速',
    progress: 80,
    stage: '撰写报告',
    owner: '李强',
    ownerAvatar: '李',
    updatedAt: '3小时前',
    deliverables: ['全球核心专利失效时间表', '临床 III 期竞品进度对比'],
    logs: [{ timestamp: '3小时前', stage: '初步分析', message: '完成专利穿透报告初稿', status: 'success' }]
  },
  {
    id: 'RES-20260819-0015',
    title: '固态电池技术可行性评估',
    opportunityId: 'OPP-20260819-025',
    opportunityName: '新型固态电池材料突破',
    progress: 30,
    stage: '资料收集',
    owner: '王明',
    ownerAvatar: '王',
    updatedAt: '4小时前',
    deliverables: ['主要材料供应商成本曲线'],
    logs: [{ timestamp: '4小时前', stage: '资料收集', message: '导入 45 篇顶会论文摘要', status: 'success' }]
  }
];

export const MOCK_MONITORING_PLANS: MonitoringPlan[] = [
  {
    id: 'PLAN-2025-001',
    name: 'AI 产业链动态监控',
    keywords: ['AI', '大模型', '算力', '知识管理', '智能体'],
    scope: '全球',
    sourceCount: 28,
    frequency: '每30分钟',
    healthScore: 98,
    status: '运行中',
    nextRun: '12 分钟后 (10:30)',
    totalRuns: 1420,
    signalCount: 845,
    alertCount: 4,
    updatedAt: '2026-08-19'
  },
  {
    id: 'PLAN-2025-002',
    name: '半导体行业监控',
    keywords: ['半导体', '芯片', 'EDA', '先进封装'],
    scope: '全球',
    sourceCount: 35,
    frequency: '每1小时',
    healthScore: 92,
    status: '运行中',
    nextRun: '32 分钟后 (10:50)',
    totalRuns: 980,
    signalCount: 512,
    alertCount: 2,
    updatedAt: '2026-08-19'
  },
  {
    id: 'PLAN-2025-003',
    name: '新能源政策与补贴追踪',
    keywords: ['新能源', '政策', '补贴', '储能', '固态电池'],
    scope: '中国',
    sourceCount: 22,
    frequency: '每2小时',
    healthScore: 68,
    status: '运行中',
    nextRun: '1 小时 12 分钟后 (11:30)',
    totalRuns: 640,
    signalCount: 288,
    alertCount: 8,
    updatedAt: '2026-08-19'
  },
  {
    id: 'PLAN-2025-004',
    name: '生物医药研发进展监控',
    keywords: ['生物医药', '临床', 'FDA', '基因编辑'],
    scope: '全球',
    sourceCount: 31,
    frequency: '每1小时',
    healthScore: 90,
    status: '运行中',
    nextRun: '45 分钟后 (11:05)',
    totalRuns: 890,
    signalCount: 420,
    alertCount: 1,
    updatedAt: '2026-08-19'
  },
  {
    id: 'PLAN-2025-005',
    name: 'Web3 与区块链动态',
    keywords: ['Web3', '区块链', '加密货币', 'Layer2'],
    scope: '全球',
    sourceCount: 18,
    frequency: '每4小时',
    healthScore: 42,
    status: '运行中',
    nextRun: '2 小时 18 分钟后 (12:38)',
    totalRuns: 450,
    signalCount: 190,
    alertCount: 12,
    updatedAt: '2026-08-19'
  }
];

export const MOCK_RUNS: RunHistoryItem[] = [
  {
    id: 'RUN-20260819-1048',
    planId: 'PLAN-2025-001',
    planName: 'AI 产业链动态监控',
    triggerType: '定时调度',
    startTime: '2026-08-19 10:00:00',
    duration: '42s',
    status: '部分失败',
    collectedCount: 48,
    newSignals: 12,
    dedupedCount: 34,
    failedSources: 2,
    stages: [
      { name: '任务调度与分发', status: 'success', duration: '2s', count: 28 },
      { name: '数据采集与抓取', status: 'failed', duration: '24s', count: 26 },
      { name: '清洗与文本抽取', status: 'success', duration: '8s', count: 48 },
      { name: '实体识别与去重', status: 'success', duration: '5s', count: 48 },
      { name: '机会初判与入库', status: 'success', duration: '3s', count: 12 }
    ]
  },
  {
    id: 'RUN-20260819-1047',
    planId: 'PLAN-2025-002',
    planName: '半导体行业监控',
    triggerType: '定时调度',
    startTime: '2026-08-19 09:50:00',
    duration: '38s',
    status: '成功',
    collectedCount: 65,
    newSignals: 18,
    dedupedCount: 47,
    failedSources: 0,
    stages: [
      { name: '任务调度与分发', status: 'success', duration: '2s', count: 35 },
      { name: '数据采集与抓取', status: 'success', duration: '20s', count: 35 },
      { name: '清洗与文本抽取', status: 'success', duration: '7s', count: 65 },
      { name: '实体识别与去重', status: 'success', duration: '6s', count: 65 },
      { name: '机会初判与入库', status: 'success', duration: '3s', count: 18 }
    ]
  },
  {
    id: 'RUN-20260819-1046',
    planId: 'PLAN-2025-001',
    planName: 'AI 产业链动态监控',
    triggerType: '手动触发',
    startTime: '2026-08-19 09:30:00',
    duration: '45s',
    status: '成功',
    collectedCount: 52,
    newSignals: 14,
    dedupedCount: 38,
    failedSources: 0,
    stages: [
      { name: '任务调度与分发', status: 'success', duration: '2s', count: 28 },
      { name: '数据采集与抓取', status: 'success', duration: '25s', count: 28 },
      { name: '清洗与文本抽取', status: 'success', duration: '9s', count: 52 },
      { name: '实体识别与去重', status: 'success', duration: '6s', count: 52 },
      { name: '机会初判与入库', status: 'success', duration: '3s', count: 14 }
    ]
  }
];

export const MOCK_QUEUE_TASKS: AnalysisQueueTask[] = [
  {
    id: 'TASK-20260819-00482',
    type: '文本向量化与实体抽取',
    target: 'TechCrunch AI Enterprise News',
    runId: 'RUN-20260819-1048',
    worker: 'worker-node-03',
    status: '失败',
    priority: 'P0',
    duration: '12s',
    createdAt: '10:01:14',
    errorReason: 'HTTP 429: API rate limit exceeded on upstream embedding endpoint'
  },
  {
    id: 'TASK-20260819-00483',
    type: '关系图谱节点关联',
    target: 'OpenAI -> Microsoft Relationship Graph',
    runId: 'RUN-20260819-1048',
    worker: 'worker-node-01',
    status: '处理中',
    priority: 'P1',
    duration: '4s',
    createdAt: '10:02:00'
  },
  {
    id: 'TASK-20260819-00484',
    type: '机会初判打分计算',
    target: '企业级AI知识管理平台',
    runId: 'RUN-20260819-1048',
    worker: 'worker-node-02',
    status: '待处理',
    priority: 'P1',
    duration: '-',
    createdAt: '10:02:15'
  }
];

export const MOCK_ALERTS: AlertItem[] = [
  {
    id: 'AL-20260819-01528',
    title: '来源同步失败 - TechCrunch',
    type: '来源同步失败',
    severity: '高',
    source: 'TechCrunch',
    time: '15分钟前',
    status: '未读',
    relatedRunId: 'RUN-20260819-1048',
    detail: 'TechCrunch RSS 源连续 3 次连接超时，可能由于反爬风控升级或 CDN 节点抖动。',
    suggestedAction: '建议检查代理节点池或切换至备用 API 抓取通道。'
  },
  {
    id: 'AL-20260819-01529',
    title: '关键词突增 - 量子计算',
    type: '关键词突增',
    severity: '中',
    source: '量子计算',
    time: '1小时前',
    status: '未读',
    detail: '过去 2 小时内相关情报数量突增 340%，主要集中于离子阱芯片实验进展。',
    suggestedAction: '建议创建专项研判机会或升级监控计划。'
  },
  {
    id: 'AL-20260819-01530',
    title: '异常趋势波动 - 碳捕集技术',
    type: '异常趋势波动',
    severity: '中',
    source: '碳捕集技术',
    time: '2小时前',
    status: '处理中',
    relatedOpportunityId: 'OPP-20260819-022',
    detail: '行业媒体讨论度与学术预印本发布出现分歧，信号热度产生异常震荡。',
    suggestedAction: '人工介入过滤噪音来源并重新校准置信度。'
  },
  {
    id: 'AL-20260819-01531',
    title: '数据处理延迟 - 分析队列积压',
    type: '数据处理延迟',
    severity: '低',
    source: '分析队列',
    time: '3小时前',
    status: '已解决',
    detail: '队列任务堆积超过 200 条，P95 处理延迟升至 45 秒。系统已自动扩容 2 个 Worker。',
    suggestedAction: '当前指标已恢复正常，持续观察资源水位。'
  },
  {
    id: 'AL-20260819-01532',
    title: '置信度下降 - 自动驾驶某自媒体来源',
    type: '置信度下降',
    severity: '低',
    source: '自动驾驶',
    time: '4小时前',
    status: '已解决',
    detail: '该数据源最近 10 条内容中有 4 条被判定为营销软文，综合质量评分降至 48 分。',
    suggestedAction: '已自动降低该来源权重至 0.2。'
  }
];

export const MOCK_MEMBERS: Member[] = [
  {
    id: 'MEM-001',
    name: '张天宇',
    email: 'zhangtianyu@radar.io',
    role: '高级分析师',
    opportunitiesCount: 14,
    researchCount: 6,
    lastActive: '刚刚',
    status: '正常',
    avatar: '张'
  },
  {
    id: 'MEM-002',
    name: '王明',
    email: 'wangming@radar.io',
    role: '分析师',
    opportunitiesCount: 8,
    researchCount: 4,
    lastActive: '5分钟前',
    status: '正常',
    avatar: '王'
  },
  {
    id: 'MEM-003',
    name: '李强',
    email: 'liqiang@radar.io',
    role: '管理员',
    opportunitiesCount: 22,
    researchCount: 9,
    lastActive: '10分钟前',
    status: '正常',
    avatar: '李'
  },
  {
    id: 'MEM-004',
    name: '赵敏',
    email: 'zhaomin@radar.io',
    role: '高级分析师',
    opportunitiesCount: 11,
    researchCount: 5,
    lastActive: '2小时前',
    status: '正常',
    avatar: '赵'
  },
  {
    id: 'MEM-005',
    name: '陈磊',
    email: 'chenlei@radar.io',
    role: '分析师',
    opportunitiesCount: 5,
    researchCount: 2,
    lastActive: '昨天',
    status: '正常',
    avatar: '陈'
  }
];

export const MOCK_INTEGRATIONS: IntegrationItem[] = [
  {
    id: 'INT-SLACK',
    name: 'Slack',
    category: 'IM 通知',
    status: 'connected',
    desc: '向 #opportunity-alerts 与 #daily-radar 频道推送高价值机会与系统告警',
    icon: 'slack',
    lastSync: '2分钟前'
  },
  {
    id: 'INT-FEISHU',
    name: '飞书 (Feishu)',
    category: 'IM 通知',
    status: 'connected',
    desc: '支持飞书群机器人卡片消息、审批流流转与多维表格同步',
    icon: 'feishu',
    lastSync: '5分钟前'
  },
  {
    id: 'INT-TEAMS',
    name: 'Microsoft Teams',
    category: 'IM 通知',
    status: 'error',
    desc: 'OAuth 凭据已于 2026-08-18 到期，Webhook 投递失败',
    icon: 'teams',
    lastSync: '18小时前',
    errorDetail: 'Invalid OAuth2 Token: Refresh token expired (code: 40103)'
  },
  {
    id: 'INT-DINGTALK',
    name: '钉钉 (DingTalk)',
    category: 'IM 通知',
    status: 'disconnected',
    desc: '通过钉钉群自定义机器人推送告警消息',
    icon: 'dingtalk',
    lastSync: '-'
  },
  {
    id: 'INT-WEBHOOK',
    name: '自定义 Webhook',
    category: '自定义 Webhook',
    status: 'connected',
    desc: '实时向企业内部数据总线广播情报与机会 JSON 事件流',
    icon: 'webhook',
    lastSync: '刚刚'
  },
  {
    id: 'INT-GITHUB',
    name: 'GitHub Enterprise',
    category: '代码与数据',
    status: 'connected',
    desc: '自动同步开源仓库 Release、Star 突增与技术动态',
    icon: 'github',
    lastSync: '10分钟前'
  }
];
