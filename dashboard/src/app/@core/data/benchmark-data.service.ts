import { Injectable } from '@angular/core';

export interface Gate {
  id: number;
  name: string;
  status: 'pass' | 'fail' | 'open' | 'pending';
  summary: string;
  evidence: string;
}

export interface ModelRun {
  model: string;
  task: string;
  score: number;
  recall: string;
  t0: string;
  label: string;
}

@Injectable({ providedIn: 'root' })
export class BenchmarkDataService {

  gates: Gate[] = [
    { id: 1, name: 'Judge discrimination', status: 'pass',
      summary: 'Deterministic instrument validation: strong control 22/22 vs weak 12/22.',
      evidence: '[REAL] results/qualification/GATE1-STEP1-NOTE.md' },
    { id: 2, name: 'Role separation', status: 'fail',
      summary: 'Mock self-test ALL GREEN; 3 real runs 0/3 — qwen2.5-1.5b cannot execute the protocol.',
      evidence: '[REAL] results/qualification/t2/GATE2-REHEARSAL-NOTE.md' },
    { id: 3, name: 'Sandbox install', status: 'pass',
      summary: 'MCP filesystem server installed in temp HOME, 41s time-to-working, T0 4/4.',
      evidence: '[REAL] results/qualification/t3/T3-REHEARSAL-REPORT.md' },
    { id: 4, name: 'Live Jev calibration', status: 'open',
      summary: 'Needs Jev API key from Sakura.',
      evidence: '[OPEN]' },
    { id: 5, name: 'Baselines', status: 'pass',
      summary: 'T1 baseline 0/22 (prompt echo); T2 baseline aborted; delta unmeasurable with this model.',
      evidence: '[REAL] results/qualification/baselines/GATE5-BASELINES-NOTE.md' },
    { id: 6, name: 'Policy demonstration', status: 'open',
      summary: 'Pending live runs.',
      evidence: '[OPEN]' },
    { id: 7, name: 'Final plural review', status: 'open',
      summary: 'Pending live runs.',
      evidence: '[OPEN]' },
  ];

  models: ModelRun[] = [
    { model: 'qwen2.5-1.5b-local', task: 'T1 open loop', score: 68.3, recall: '0/22', t0: '3/3', label: '[REAL]' },
    { model: 'llama3.2-1b-local', task: 'T1 open loop', score: 85.7, recall: '0/22', t0: '2/3', label: '[REAL]' },
    { model: 'qwen2.5-1.5b-local', task: 'T2 rehearsal', score: 0, recall: 'n/a', t0: '0/3', label: '[REAL]' },
  ];

  stats = [
    { title: 'Suite tests green', value: '100/100', icon: 'checkmark-circle-2-outline', status: 'success' },
    { title: 'Gates qualified', value: '3 / 7', icon: 'shield-outline', status: 'warning' },
    { title: 'Models looped', value: '2', icon: 'cpu-outline', status: 'info' },
    { title: 'Evidence labels', value: '[REAL]', icon: 'award-outline', status: 'primary' },
  ];

  gateChartOption(): any {
    const counts = { pass: 0, fail: 0, open: 0, pending: 0 };
    this.gates.forEach(g => counts[g.status]++);
    return {
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        data: [
          { value: counts.pass, name: 'Pass', itemStyle: { color: '#00d68f' } },
          { value: counts.fail, name: 'Fail', itemStyle: { color: '#ff3d71' } },
          { value: counts.open, name: 'Open', itemStyle: { color: '#ffaa00' } },
          { value: counts.pending, name: 'Pending', itemStyle: { color: '#8f9bb3' } },
        ],
        label: { color: '#8f9bb3' },
      }],
    };
  }

  modelChartOption(): any {
    return {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: this.models.map(m => m.model.split('-')[0]) },
      yAxis: { type: 'value', max: 100 },
      series: [{
        type: 'bar',
        data: this.models.map(m => m.score),
        itemStyle: { color: '#3366ff' },
        label: { show: true, position: 'top', color: '#8f9bb3' },
      }],
    };
  }
}
