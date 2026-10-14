import React, { useState } from 'react';
import {
  Pause,
  XCircle,
  MoreHorizontal,
  Check,
  ChevronRight,
  AlertCircle,
  Play,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { useRouter } from '../router/RouterContext';

export const P12_ResearchWorkflowDetail: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [isPaused, setIsPaused] = useState(false);

  const steps = [
    { num: 1, title: '问题定义', status: 'completed' },
    { num: 2, title: '资料收集', status: 'completed' },
    { num: 3, title: '假设分析', status: 'current' },
    { num: 4, title: '验证', status: 'pending' },
    { num: 5, title: '结论', status: 'pending' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '研究', path: '/research' },
          { label: '研究工作流详情' },
        ]}
        title="企业级AI知识管理平台研究"
        subtitle="负责人: 张天宇 · 创建时间: 2025-05-13 14:20 · 预计完成: 2025-05-20"
        actions={
          <>
            <button
              onClick={() => {
                setIsPaused(!isPaused);
                showToast(isPaused ? '研究已恢复运行' : '研究工作流已暂停', 'info');
              }}
              className="btn btn-secondary"
            >
              <Pause size={14} />
              <span>{isPaused ? '恢复' : '暂停'}</span>
            </button>
            <button
              onClick={() => openState('P12-S01')}
              className="btn btn-secondary"
              style={{ color: 'var(--color-danger)', borderColor: 'var(--color-danger-border)' }}
            >
              <AlertCircle size={14} />
              <span>异常与恢复</span>
            </button>
            <button
              onClick={() => showToast('已取消该研究工作流', 'info')}
              className="btn btn-secondary"
            >
              <XCircle size={14} />
              <span>取消</span>
            </button>
          </>
        }
      />

      {/* Top 3 Progress / Duration Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 20 }}>
        <div className="card" style={{ padding: '18px 24px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 8 }}>整体进度</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
              60%
            </span>
            <div style={{ flex: 1, height: 8, borderRadius: 4, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
              <div style={{ width: '60%', height: '100%', backgroundColor: 'var(--color-primary)' }} />
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '18px 24px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 8 }}>已用时间</div>
          <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
            2天5小时
          </div>
        </div>

        <div className="card" style={{ padding: '18px 24px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 8 }}>预计剩余</div>
          <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
            2天
          </div>
        </div>
      </div>

      {/* Stepper Card */}
      <div className="card" style={{ padding: '24px 32px', marginBottom: 20 }}>
        <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 20 }}>
          研究步骤
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'relative' }}>
          {/* Background Connecting Line */}
          <div
            style={{
              position: 'absolute',
              top: 18,
              left: 40,
              right: 40,
              height: 2,
              backgroundColor: '#e2e8f0',
              zIndex: 1,
            }}
          />

          {steps.map((step) => {
            const isCompleted = step.status === 'completed';
            const isCurrent = step.status === 'current';

            return (
              <div
                key={step.num}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                  position: 'relative',
                  zIndex: 2,
                }}
              >
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    backgroundColor: isCompleted ? 'var(--color-success)' : isCurrent ? 'var(--color-primary)' : '#ffffff',
                    color: isCompleted || isCurrent ? '#ffffff' : 'var(--text-muted)',
                    border: isCompleted || isCurrent ? 'none' : '2px solid #cbd5e1',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: 'var(--font-size-sm)',
                    boxShadow: isCurrent ? '0 0 0 4px var(--color-primary-light)' : undefined,
                  }}
                >
                  {isCompleted ? <Check size={18} strokeWidth={3} /> : step.num}
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {step.title}
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: isCompleted ? 'var(--color-success)' : isCurrent ? 'var(--color-primary)' : 'var(--text-muted)',
                      marginTop: 2,
                    }}
                  >
                    {isCompleted ? '已完成' : isCurrent ? '进行中' : '待开始'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main 3-Column Split: Current Step + Research Info + Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 16, marginBottom: 20 }}>
        {/* Card 1: 当前步骤: 假设分析 */}
        <div className="card">
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
            当前步骤 : 假设分析
          </h3>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 16, backgroundColor: '#f8fafc', padding: '8px 12px', borderRadius: 'var(--radius-md)' }}>
            基于已收集的资料，形成关键假设并评估其证据强度。
          </p>

          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
            关键任务
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { task: '分析市场容量和增长', status: '完成 3/3', done: true },
              { task: '评估技术可行性', status: '完成 2/4', done: true },
              { task: '梳理竞争格局', status: '完成 1/3', done: true },
              { task: '验证商业模式', status: '待开始 0/2', done: false },
            ].map((t, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input type="checkbox" checked={t.done} readOnly />
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-primary)' }}>{t.task}</span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Card 2: 研究信息 */}
        <div className="card">
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
            研究信息
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 'var(--font-size-xs)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>研究类型</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>机会研究</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>关联机会</span>
              <span
                onClick={() => navigate('/opportunities/OPP-20260819-021')}
                style={{ color: 'var(--color-primary)', cursor: 'pointer', fontWeight: 500 }}
              >
                企业级AI知识管理平台
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>研究领域</span>
              <span style={{ color: 'var(--text-primary)' }}>AI 应用</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>研究方法</span>
              <span style={{ color: 'var(--text-primary)' }}>定性分析 + 定量分析</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>数据来源</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>32 个</span>
            </div>
          </div>
        </div>

        {/* Card 3: 最近活动 */}
        <div className="card">
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
            最近活动
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { action: '资料收集完成', time: '2025-05-15 10:30' },
              { action: '开始假设分析', time: '2025-05-15 14:20' },
              { action: '市场规模分析完成', time: '2025-05-15 16:45' },
            ].map((act, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--color-primary)', marginTop: 5, flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {act.action}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>
                    {act.time}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Card: 下一步与操作 */}
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '18px 24px',
        }}
      >
        <div>
          <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
            下一步 : 验证
          </h4>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
            验证关键假设，补齐证据并形成最终研究结论。
          </p>
        </div>

        <button
          onClick={() => navigate('/research/RES-20260819-0011/result')}
          className="btn btn-primary btn-lg"
        >
          <span>查看研究结论</span>
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};
