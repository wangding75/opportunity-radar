import React, { lazy, Suspense } from 'react';
import { useRouter } from './router/RouterContext';
import { AppShell } from './components/shell/AppShell';
import { ToastContainer } from './components/common/Toast';
import { StateOverlays } from './components/states/StateOverlays';

// Route-level loading keeps the initial shell small and isolates page failures.
const P01_TodayRadar = lazy(() => import('./pages/P01_TodayRadar').then(m => ({ default: m.P01_TodayRadar })));
const P02_IntelligenceList = lazy(() => import('./pages/P02_IntelligenceList').then(m => ({ default: m.P02_IntelligenceList })));
const P03_IntelligenceDetail = lazy(() => import('./pages/P03_IntelligenceDetail').then(m => ({ default: m.P03_IntelligenceDetail })));
const P04_KeywordDiscovery = lazy(() => import('./pages/P04_KeywordDiscovery').then(m => ({ default: m.P04_KeywordDiscovery })));
const P05_TrackedKeywords = lazy(() => import('./pages/P05_TrackedKeywords').then(m => ({ default: m.P05_TrackedKeywords })));
const P06_TrendAnalysis = lazy(() => import('./pages/P06_TrendAnalysis').then(m => ({ default: m.P06_TrendAnalysis })));
const P07_RelationGraph = lazy(() => import('./pages/P07_RelationGraph').then(m => ({ default: m.P07_RelationGraph })));
const P08_OpportunityPool = lazy(() => import('./pages/P08_OpportunityPool').then(m => ({ default: m.P08_OpportunityPool })));
const P09_OpportunityDetail = lazy(() => import('./pages/P09_OpportunityDetail').then(m => ({ default: m.P09_OpportunityDetail })));
const P10_StructuredAnalysis = lazy(() => import('./pages/P10_StructuredAnalysis').then(m => ({ default: m.P10_StructuredAnalysis })));
const P11_ResearchWorkflow = lazy(() => import('./pages/P11_ResearchWorkflow').then(m => ({ default: m.P11_ResearchWorkflow })));
const P12_ResearchWorkflowDetail = lazy(() => import('./pages/P12_ResearchWorkflowDetail').then(m => ({ default: m.P12_ResearchWorkflowDetail })));
const P13_ResearchResult = lazy(() => import('./pages/P13_ResearchResult').then(m => ({ default: m.P13_ResearchResult })));
const P14_Sources = lazy(() => import('./pages/P14_Sources').then(m => ({ default: m.P14_Sources })));
const P15_SourceDetail = lazy(() => import('./pages/P15_SourceDetail').then(m => ({ default: m.P15_SourceDetail })));
const P16_SourceHealth = lazy(() => import('./pages/P16_SourceHealth').then(m => ({ default: m.P16_SourceHealth })));
const P17_MonitoringPlans = lazy(() => import('./pages/P17_MonitoringPlans').then(m => ({ default: m.P17_MonitoringPlans })));
const P18_MonitoringPlanDetail = lazy(() => import('./pages/P18_MonitoringPlanDetail').then(m => ({ default: m.P18_MonitoringPlanDetail })));
const P19_RunHistory = lazy(() => import('./pages/P19_RunHistory').then(m => ({ default: m.P19_RunHistory })));
const P20_RunDetail = lazy(() => import('./pages/P20_RunDetail').then(m => ({ default: m.P20_RunDetail })));
const P21_AnalysisQueue = lazy(() => import('./pages/P21_AnalysisQueue').then(m => ({ default: m.P21_AnalysisQueue })));
const P22_AlertCenter = lazy(() => import('./pages/P22_AlertCenter').then(m => ({ default: m.P22_AlertCenter })));
const P23_AlertRules = lazy(() => import('./pages/P23_AlertRules').then(m => ({ default: m.P23_AlertRules })));
const P24_WorkspaceSettings = lazy(() => import('./pages/P24_WorkspaceSettings').then(m => ({ default: m.P24_WorkspaceSettings })));
const P25_MemberManagement = lazy(() => import('./pages/P25_MemberManagement').then(m => ({ default: m.P25_MemberManagement })));
const P26_RolesAndPermissions = lazy(() => import('./pages/P26_RolesAndPermissions').then(m => ({ default: m.P26_RolesAndPermissions })));
const P27_AccountSecurity = lazy(() => import('./pages/P27_AccountSecurity').then(m => ({ default: m.P27_AccountSecurity })));
const P28_ExternalIntegrations = lazy(() => import('./pages/P28_ExternalIntegrations').then(m => ({ default: m.P28_ExternalIntegrations })));
const P29_AuditLogs = lazy(() => import('./pages/P29_AuditLogs').then(m => ({ default: m.P29_AuditLogs })));
const P30_SystemDiagnostics = lazy(() => import('./pages/P30_SystemDiagnostics').then(m => ({ default: m.P30_SystemDiagnostics })));
const P31_GlobalSearch = lazy(() => import('./pages/P31_GlobalSearch').then(m => ({ default: m.P31_GlobalSearch })));
const P32_Login = lazy(() => import('./pages/P32_Login').then(m => ({ default: m.P32_Login })));
const P33_AccessDenied = lazy(() => import('./pages/P33_AccessDenied').then(m => ({ default: m.P33_AccessDenied })));
const P34_NotFound = lazy(() => import('./pages/P34_NotFound').then(m => ({ default: m.P34_NotFound })));

export const App: React.FC = () => {
  const { currentRoute } = useRouter();

  // Render the page body matching current route
  const renderPageComponent = () => {
    switch (currentRoute.id) {
      case 'P01': return <P01_TodayRadar />;
      case 'P02': return <P02_IntelligenceList />;
      case 'P03': return <P03_IntelligenceDetail />;
      case 'P04': return <P04_KeywordDiscovery />;
      case 'P05': return <P05_TrackedKeywords />;
      case 'P06': return <P06_TrendAnalysis />;
      case 'P07': return <P07_RelationGraph />;
      case 'P08': return <P08_OpportunityPool />;
      case 'P09': return <P09_OpportunityDetail />;
      case 'P10': return <P10_StructuredAnalysis />;
      case 'P11': return <P11_ResearchWorkflow />;
      case 'P12': return <P12_ResearchWorkflowDetail />;
      case 'P13': return <P13_ResearchResult />;
      case 'P14': return <P14_Sources />;
      case 'P15': return <P15_SourceDetail />;
      case 'P16': return <P16_SourceHealth />;
      case 'P17': return <P17_MonitoringPlans />;
      case 'P18': return <P18_MonitoringPlanDetail />;
      case 'P19': return <P19_RunHistory />;
      case 'P20': return <P20_RunDetail />;
      case 'P21': return <P21_AnalysisQueue />;
      case 'P22': return <P22_AlertCenter />;
      case 'P23': return <P23_AlertRules />;
      case 'P24': return <P24_WorkspaceSettings />;
      case 'P25': return <P25_MemberManagement />;
      case 'P26': return <P26_RolesAndPermissions />;
      case 'P27': return <P27_AccountSecurity />;
      case 'P28': return <P28_ExternalIntegrations />;
      case 'P29': return <P29_AuditLogs />;
      case 'P30': return <P30_SystemDiagnostics />;
      case 'P31': return <P31_GlobalSearch />;
      case 'P32': return <P32_Login />;
      case 'P33': return <P33_AccessDenied />;
      case 'P34': return <P34_NotFound />;
      default: return <P01_TodayRadar />;
    }
  };

  const pageComponent = renderPageComponent();

  return (
    <>
      <Suspense fallback={<div className="route-loading" role="status">正在加载页面…</div>}>
      {currentRoute.shell === 'AUTH_SHELL' ? (
        /* P32 Login has standalone split screen auth layout */
        pageComponent
      ) : (
        /* All other pages use unified standard AppShell */
        <AppShell>
          {pageComponent}
        </AppShell>
      )}
      </Suspense>

      {/* Global Modals & Drawers */}
      <StateOverlays />

      {/* Global Toast Feedback */}
      <ToastContainer />
    </>
  );
};
