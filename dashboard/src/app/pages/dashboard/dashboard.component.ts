import { Component, OnDestroy } from '@angular/core';
import { NbThemeService } from '@nebular/theme';
import { BenchmarkDataService } from '../../@core/data/benchmark-data.service';

@Component({
  selector: 'ngx-dashboard',
  styleUrls: ['./dashboard.component.scss'],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnDestroy {
  stats = this.data.stats;
  gateChart: any;
  modelChart: any;
  themeSubscription: any;

  constructor(private theme: NbThemeService,
              private data: BenchmarkDataService) {
    this.themeSubscription = this.theme.getJsTheme().subscribe(() => {
      this.gateChart = this.data.gateChartOption();
      this.modelChart = this.data.modelChartOption();
    });
  }

  ngOnDestroy(): void {
    this.themeSubscription.unsubscribe();
  }
}
