import React, { useState } from 'react';
import {
  Drawer,
} from '../common/Drawer';
import {
  Modal,
} from '../common/Modal';
import {
  useRouter,
} from '../../router/RouterContext';
import {
  Briefcase,
  Activity,
  Share2,
  Trash2,
  User,
  Link,
  Sparkles,
  BookOpen,
  AlertTriangle,
  Send,
  Play,
  RotateCw,
  Sliders,
  Shield,
  Key,
  Lock,
  Plus,
  Zap,
} from 'lucide-react';

export const StateOverlays: React.FC = () => {
  const { currentState, closeState, openState, navigate, showToast } = useRouter();

  if (!currentState) return null;

  return (
    <>
      {/* P03-S01: 从情报创建机会 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P03-S01'}
        onClose={closeState}
        title="从情报创建机会"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('已基于情报成功创建机会 OPP-20260819-021', 'success');
                closeState();
                navigate('/opportunities/OPP-20260819-021');
              }}
              className="btn btn-primary"
            >
              确认创建机会
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ padding: 12, borderRadius: 6, backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', fontSize: '12px', color: '#1e40af' }}>
            系统已自动从情报「微软宣布投资 OpenAI 100亿美元」提取实体与关键事实作为机会初始化数据。
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 6 }}>机会名称</label>
            <input type="text" defaultValue="企业级 AI 知识管理与助手协同平台" className="input-base" style={{ width: '100%' }} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 6 }}>所属领域</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>人工智能 / 企业服务</option>
                <option>新能源</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 6 }}>优先级</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>高优先级</option>
                <option>中优先级</option>
                <option>低优先级</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 6 }}>初始评估摘要</label>
            <textarea
              rows={4}
              defaultValue="伴随大模型基础底座能力跃升，企业知识库与生产力场景融合加速。具备私有化部署和高可信合规的企业服务产品出现明显商业化窗口。"
              className="input-base"
              style={{ width: '100%', resize: 'vertical' }}
            />
          </div>
        </div>
      </Drawer>

      {/* P03-S02: 加入监控计划 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P03-S02'}
        onClose={closeState}
        title="将情报加入监控计划"
        width={500}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('已成功关联至监控计划 PLAN-2025-001', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              确认加入
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>选择要关联的已有监控计划：</div>
          {[
            { id: 'PLAN-2025-001', name: 'AI 产业链动态监控', count: '28 来源' },
            { id: 'PLAN-2025-002', name: '全球大模型开源生态', count: '14 来源' },
            { id: 'PLAN-2025-003', name: '半导体先进制程追踪', count: '19 来源' },
          ].map((p, idx) => (
            <label key={p.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-default)', cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input type="radio" name="monPlan" defaultChecked={idx === 0} />
                <span style={{ fontSize: '12px', fontWeight: 600 }}>{p.name}</span>
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{p.count}</span>
            </label>
          ))}
        </div>
      </Drawer>

      {/* P03-S03: 分享 / 导出情报 (Modal) */}
      <Modal
        isOpen={currentState === 'P03-S03'}
        onClose={closeState}
        title="分享与导出情报"
        width={480}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">关闭</button>
            <button
              onClick={() => {
                showToast('情报链接已复制到剪贴板', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              复制分享链接
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '12px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>公开链接</label>
            <input type="text" readOnly value="https://radar.company.com/intelligence/INT-20260819-01842" className="input-base" style={{ width: '100%', fontSize: '12px' }} />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => showToast('已导出 Markdown', 'info')} className="btn btn-secondary btn-sm" style={{ flex: 1 }}>导出 Markdown</button>
            <button onClick={() => showToast('已导出 PDF 报告', 'info')} className="btn btn-secondary btn-sm" style={{ flex: 1 }}>导出 PDF</button>
          </div>
        </div>
      </Modal>

      {/* P03-S04: 忽略情报信号 (Modal) */}
      <Modal
        isOpen={currentState === 'P03-S04'}
        onClose={closeState}
        title="忽略情报信号"
        width={440}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('已忽略该情报，后续将减少同类推荐', 'info');
                closeState();
                navigate('/intelligence');
              }}
              className="btn btn-primary"
              style={{ backgroundColor: 'var(--color-danger)' }}
            >
              确认忽略
            </button>
          </div>
        }
      >
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          忽略后，该情报将从活跃列表移入「已忽略」，并且算法将降低同类主题的推荐权重。
        </p>
      </Modal>

      {/* P09-S01: 修改机会状态 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P09-S01'}
        onClose={closeState}
        title="修改机会状态"
        width={460}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('机会状态已更新为「研判中」', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              保存修改
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: '12px' }}>
          {['新发现', '研判中', '持续跟踪', '已立项', '已忽略', '已归档'].map((s) => (
            <label key={s} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', borderRadius: 4, border: '1px solid var(--border-default)', cursor: 'pointer' }}>
              <input type="radio" name="oppState" defaultChecked={s === '研判中'} />
              <span style={{ fontWeight: 600 }}>{s}</span>
            </label>
          ))}
        </div>
      </Drawer>

      {/* P09-S02: 分配负责人 (Modal) */}
      <Modal
        isOpen={currentState === 'P09-S02'}
        onClose={closeState}
        title="分配机会负责人"
        width={440}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('已成功指定负责人为「张天宇」', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              确认分配
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
          {['张天宇 (高级分析师)', '李想 (高级研究员)', '王明 (工作区管理员)', '陈晨 (分析师)'].map((u, i) => (
            <label key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', borderRadius: 4, border: '1px solid var(--border-default)', cursor: 'pointer' }}>
              <input type="radio" name="assignee" defaultChecked={i === 0} />
              <span>{u}</span>
            </label>
          ))}
        </div>
      </Modal>

      {/* P09-S04: 结构化分析 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P09-S04'}
        onClose={closeState}
        title="机会结构化多维评估"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">关闭</button>
            <button
              onClick={() => {
                showToast('分析维度更新已保存', 'success');
                closeState();
                navigate('/opportunities/OPP-20260819-021/analysis');
              }}
              className="btn btn-primary"
            >
              查看完整分析
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, fontSize: '12px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>市场吸引力评分 (85/100)</label>
            <input type="range" min="0" max="100" defaultValue="85" style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>需求确定性 (80/100)</label>
            <input type="range" min="0" max="100" defaultValue="80" style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>进入壁垒评估</label>
            <input type="text" defaultValue="大模型微调技术 + 专有领域文档数据飞轮" className="input-base" style={{ width: '100%' }} />
          </div>
        </div>
      </Drawer>

      {/* P09-S05 / P11-S01: 启动研究工作流 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P09-S05' || currentState === 'P11-S01'}
        onClose={closeState}
        title="新建研究工作流"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('研究工作流 RES-20260819-0011 已启动', 'success');
                closeState();
                navigate('/research/RES-20260819-0011');
              }}
              className="btn btn-primary"
            >
              确认启动研究
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>研究工作流名称</label>
            <input type="text" defaultValue="企业级AI知识管理平台商业路径研究" className="input-base" style={{ width: '100%' }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>研究深度</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>标准深度 (5步闭环)</option>
                <option>快速洞察 (3步)</option>
                <option>深度尽调 (7步)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>主导研究员</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>张天宇 (高级分析师)</option>
                <option>李想</option>
              </select>
            </div>
          </div>
        </div>
      </Drawer>

      {/* P12-S01: 研究异常与恢复 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P12-S01'}
        onClose={closeState}
        title="研究步骤异常与恢复"
        width={520}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">关闭</button>
            <button
              onClick={() => {
                showToast('已重试假设分析步骤，任务重新运行中', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              重试该步骤
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '12px' }}>
          <div style={{ padding: 12, borderRadius: 6, backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c' }}>
            <strong>异常检测：</strong> 外部数据源返回了非结构化错误响应，导致第3步「假设分析」部分指标计算中断。
          </div>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>建议处置：</div>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              1. 切换备用 LLM 结构化提取管道；<br />
              2. 忽略损坏的 2 条新闻样本并强制继续；<br />
              3. 重新调度 Worker 进行全量重新评估。
            </p>
          </div>
        </div>
      </Drawer>

      {/* P13-S01: 发布研究结论 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P13-S01'}
        onClose={closeState}
        title="发布研究结论"
        width={540}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('研究结论已成功发布并同步通知团队', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              确认发布
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>结论标题</label>
            <input type="text" defaultValue="AI Agent在企业知识管理领域的应用趋势与切入点" className="input-base" style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>核心判断</label>
            <textarea rows={4} defaultValue="企业级知识库结合自主 Agent 是确定性高增长赛道，建议团队在 Q3 完成 POC 验证。" className="input-base" style={{ width: '100%' }} />
          </div>
        </div>
      </Drawer>

      {/* P17-S01: 新建监控计划 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P17-S01'}
        onClose={closeState}
        title="新建监控计划"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('监控计划 PLAN-2025-001 已创建并激活', 'success');
                closeState();
                navigate('/monitoring/PLAN-2025-001');
              }}
              className="btn btn-primary"
            >
              保存并启动监控
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>计划名称</label>
            <input type="text" defaultValue="大模型开源生态与代码库追踪" className="input-base" style={{ width: '100%' }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>执行频率</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>每 15 分钟</option>
                <option>每 30 分钟</option>
                <option>每小时</option>
                <option>每天</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>默认通知渠道</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>企业微信 + 站内信</option>
                <option>Slack</option>
                <option>Webhook</option>
              </select>
            </div>
          </div>
        </div>
      </Drawer>

      {/* P17-S02: 从模板选择监控计划 (Modal) */}
      <Modal
        isOpen={currentState === 'P17-S02'}
        onClose={closeState}
        title="选择监控计划模板"
        width={600}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('已加载行业情报监控模板', 'success');
                closeState();
                openState('P17-S01');
              }}
              className="btn btn-primary"
            >
              使用该模板
            </button>
          </div>
        }
      >
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[
            { title: '科技行业热点追踪', desc: '预置 12 个全球科技媒体与创投数据库，高频捕获最新产品动态。' },
            { title: '竞品与投融资异动', desc: '跟踪特定领域公司融资事件、高管变动与专利申请。' },
            { title: '学术与论文前沿追踪', desc: '持续监控 ArXiv、ACL 等顶会与学术平台突破。' },
            { title: '政策与监管合规监控', desc: '监控全球各国对 AI、数据安全政策发布。' },
          ].map((t, idx) => (
            <div key={idx} style={{ padding: '12px', borderRadius: 6, border: '1px solid var(--border-default)', backgroundColor: '#fafbfc', cursor: 'pointer' }}>
              <div style={{ fontWeight: 600, fontSize: '12px', marginBottom: 4 }}>{t.title}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{t.desc}</div>
            </div>
          ))}
        </div>
      </Modal>

      {/* P17-S03: 手动运行监控计划 (Drawer) -> leads to P20 */}
      <Drawer
        isOpen={currentState === 'P17-S03'}
        onClose={closeState}
        title="手动触发监控执行"
        width={500}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('手动执行已启动，正在跳转至运行详情', 'success');
                closeState();
                navigate('/runs/RUN-20260610-0950');
              }}
              className="btn btn-primary"
            >
              立即开始执行
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '12px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>指定运行的数据源范围</label>
            <select className="input-base" style={{ width: '100%' }}>
              <option>全量来源 (28 个)</option>
              <option>仅高优先级媒体 (8 个)</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>是否强制跳过缓存并重新抓取</label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
              <input type="checkbox" defaultChecked />
              <span>是，强制全量爬取与分析</span>
            </label>
          </div>
        </div>
      </Drawer>

      {/* P22-S01: 告警详情 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P22-S01'}
        onClose={closeState}
        title="告警事件处理"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">关闭</button>
            <button
              onClick={() => {
                showToast('告警已标记为「已解决」', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              标记为已解决
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '12px' }}>
          <div style={{ padding: '12px', borderRadius: 6, backgroundColor: '#fef2f2', border: '1px solid #fecaca' }}>
            <div style={{ fontWeight: 700, color: '#b91c1c', fontSize: '13px', marginBottom: 4 }}>来源 TechCrunch 抓取失败 (连续 12 次)</div>
            <div style={{ color: '#7f1d1d' }}>告警 ID: AL-20260610-01528 · 严重级别: 严重 · 触发时间: 10:24:12</div>
          </div>

          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>异常诊断信息：</div>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, backgroundColor: '#f8fafc', padding: 8, borderRadius: 4, fontFamily: 'monospace', fontSize: '12px' }}>
              HTTP 429 Too Many Requests (Rate Limit Exceeded)<br />
              IP 101.88.12.34 被目标端限流，建议调大重试退避间隔或轮换代理 IP。
            </p>
          </div>
        </div>
      </Drawer>

      {/* P23-S01: 新建 / 编辑告警规则 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P23-S01'}
        onClose={closeState}
        title="配置告警规则"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('告警规则已成功保存并启用', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              保存告警规则
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>规则名称</label>
            <input type="text" defaultValue="来源成功率低于阈值告警" className="input-base" style={{ width: '100%' }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>监控对象</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>数据来源</option>
                <option>处理队列</option>
                <option>机会评分</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>严重级别</label>
              <select className="input-base" style={{ width: '100%' }}>
                <option>高</option>
                <option>中</option>
                <option>低</option>
              </select>
            </div>
          </div>
        </div>
      </Drawer>

      {/* P25-S01: 邀请成员 (Modal) */}
      <Modal
        isOpen={currentState === 'P25-S01'}
        onClose={closeState}
        title="邀请新成员加入工作区"
        width={480}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('邀请邮件已成功发送', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              发送邀请
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>成员邮箱</label>
            <input type="email" placeholder="name@company.com" className="input-base" style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: 4 }}>初始角色</label>
            <select className="input-base" style={{ width: '100%' }}>
              <option>分析师 (Analyst)</option>
              <option>研究员</option>
              <option>工作区管理员</option>
            </select>
          </div>
        </div>
      </Modal>

      {/* P26-S01: 修改角色权限 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P26-S01'}
        onClose={closeState}
        title="配置角色权限"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('角色权限已更新', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              保存权限配置
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '12px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>角色名称</label>
            <input type="text" defaultValue="高级分析师 (Senior Analyst)" className="input-base" style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>权限细项</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}><input type="checkbox" defaultChecked /> 允许创建并修改机会</label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}><input type="checkbox" defaultChecked /> 允许启动和编辑研究工作流</label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}><input type="checkbox" defaultChecked /> 允许配置监控计划与告警规则</label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}><input type="checkbox" /> 允许管理工作区成员与计费</label>
            </div>
          </div>
        </div>
      </Drawer>

      {/* P27-S01: 开启 MFA (Modal) -> returns to P27 */}
      <Modal
        isOpen={currentState === 'P27-S01'}
        onClose={closeState}
        title="开启双重验证 (MFA)"
        width={460}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('双重验证 (MFA) 已成功开通！', 'success');
                closeState();
                navigate('/settings/security');
              }}
              className="btn btn-primary"
            >
              验证并开通
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, textAlign: 'center', fontSize: '12px' }}>
          <div style={{ width: 140, height: 140, backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>[ Authenticator QR Code ]</span>
          </div>
          <p style={{ color: 'var(--text-secondary)' }}>请使用 Authenticator 扫描上方二维码，并输入 6 位动态验证码：</p>
          <input type="text" maxLength={6} placeholder="123456" className="input-base" style={{ width: 160, height: 38, textAlign: 'center', fontSize: '18px', letterSpacing: 4, fontWeight: 700 }} />
        </div>
      </Modal>

      {/* P27-S02: 账户危险操作 (Drawer) */}
      <Drawer
        isOpen={currentState === 'P27-S02'}
        onClose={closeState}
        title="账户安全危险操作"
        width={500}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">关闭</button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '12px' }}>
          <div style={{ padding: 12, borderRadius: 6, backgroundColor: '#fef2f2', border: '1px solid #fecaca' }}>
            <div style={{ fontWeight: 700, color: '#b91c1c', marginBottom: 4 }}>注销其他所有设备会话</div>
            <button onClick={() => { showToast('其他设备会话已全部注销', 'success'); closeState(); }} className="btn btn-secondary btn-sm" style={{ marginTop: 6 }}>确认注销其他设备</button>
          </div>
          <div style={{ padding: 12, borderRadius: 6, backgroundColor: '#fef2f2', border: '1px solid #fecaca' }}>
            <div style={{ fontWeight: 700, color: '#b91c1c', marginBottom: 4 }}>重置双重验证 (MFA)</div>
            <button onClick={() => { showToast('MFA 已重置，请重新绑定', 'info'); closeState(); }} className="btn btn-secondary btn-sm" style={{ marginTop: 6 }}>确认重置 MFA</button>
          </div>
        </div>
      </Drawer>

      {/* P28-S01: 外部集成授权与修复 (Drawer over P28 parent) */}
      <Drawer
        isOpen={currentState === 'P28-S01'}
        onClose={closeState}
        title="修复外部集成授权"
        width={560}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('外部集成 OAuth 重新授权成功！', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              重新授权并连接
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '12px' }}>
          <div style={{ padding: 12, borderRadius: 6, backgroundColor: '#fffbeb', border: '1px solid #fde68a', color: '#92400e' }}>
            <strong>授权失效提醒：</strong> 钉钉/Notion 的访问令牌已过期，导致通知与同步暂停。
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>Webhook / App Key</label>
            <input type="text" defaultValue="https://oapi.dingtalk.com/robot/send?access_token=9a8f..." className="input-base" style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>加签密钥 (Secret)</label>
            <input type="password" defaultValue="SEC_a9f8b7c6..." className="input-base" style={{ width: '100%' }} />
          </div>
        </div>
      </Drawer>

      {/* P33-S01: 申请访问权限 (Modal) */}
      <Modal
        isOpen={currentState === 'P33-S01'}
        onClose={closeState}
        title="申请访问受限资源"
        width={480}
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={closeState} className="btn btn-secondary">取消</button>
            <button
              onClick={() => {
                showToast('访问权限申请已提交，管理员将收到审批通知', 'success');
                closeState();
              }}
              className="btn btn-primary"
            >
              提交权限申请
            </button>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: '12px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>申请理由</label>
            <textarea rows={3} placeholder="请说明您需要查看该机会详情的业务原因..." className="input-base" style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 4 }}>申请权限级别</label>
            <select className="input-base" style={{ width: '100%' }}>
              <option>只读查看 (Viewer)</option>
              <option>编辑与跟进 (Analyst)</option>
            </select>
          </div>
        </div>
      </Modal>
    </>
  );
};
