import { Component } from '@angular/core';
import { LocalDataSource } from 'ng2-smart-table';
import { BenchmarkDataService } from '../../@core/data/benchmark-data.service';

@Component({
  selector: 'ngx-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.scss'],
})
export class ResultsComponent {
  settings = {
    actions: false,
    columns: {
      model: { title: 'Model', type: 'string' },
      task: { title: 'Task', type: 'string' },
      score: { title: 'Score', type: 'number' },
      recall: { title: 'Recall', type: 'string' },
      t0: { title: 'T0 pass', type: 'string' },
      label: { title: 'Evidence', type: 'string' },
    },
  };

  source: LocalDataSource = new LocalDataSource();

  constructor(private data: BenchmarkDataService) {
    this.source.load(this.data.models);
  }
}
