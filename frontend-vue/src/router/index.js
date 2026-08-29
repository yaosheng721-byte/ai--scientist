import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import CreateRunView from '../views/CreateRunView.vue'
import DatasetProfileView from '../views/DatasetProfileView.vue'
import ExperimentsView from '../views/ExperimentsView.vue'
import HumanReviewView from '../views/HumanReviewView.vue'
import HypothesisScoreView from '../views/HypothesisScoreView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import ReportView from '../views/ReportView.vue'
import ResultPoolView from '../views/ResultPoolView.vue'
import ToolLogsView from '../views/ToolLogsView.vue'
import WorkflowView from '../views/WorkflowView.vue'
import WorkspaceView from '../views/WorkspaceView.vue'

const routes = [
  {
    path: '/',
    component: AppShell,
    children: [
      { path: '', redirect: '/new' },
      { path: 'new', name: 'create-run', component: CreateRunView },
      { path: 'workspace/:runId?', name: 'workspace', component: WorkspaceView },
      { path: 'runs/:runId/workflow', name: 'workflow', component: WorkflowView },
      { path: 'runs/:runId/dataset', name: 'dataset-profile', component: DatasetProfileView },
      { path: 'runs/:runId/tools', name: 'tool-logs', component: ToolLogsView },
      { path: 'runs/:runId/pools', name: 'result-pool', component: ResultPoolView },
      { path: 'runs/:runId/scores', name: 'hypothesis-score', component: HypothesisScoreView },
      { path: 'runs/:runId/review', name: 'human-review', component: HumanReviewView },
      { path: 'runs/:runId/experiments', name: 'experiments', component: ExperimentsView },
      { path: 'runs/:runId/report', name: 'report', component: ReportView },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
