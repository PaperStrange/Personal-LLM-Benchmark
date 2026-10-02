import { Component } from '@angular/core';
import { BenchmarkDataService, Gate } from '../../@core/data/benchmark-data.service';

@Component({
  selector: 'ngx-gates',
  templateUrl: './gates.component.html',
  styleUrls: ['./gates.component.scss'],
})
export class GatesComponent {
  gates: Gate[] = this.data.gates;

  statusIcon = {
    pass: 'checkmark-circle-2-outline',
    fail: 'close-circle-outline',
    open: 'radio-button-off-outline',
    pending: 'clock-outline',
  };

  constructor(private data: BenchmarkDataService) {}
}
