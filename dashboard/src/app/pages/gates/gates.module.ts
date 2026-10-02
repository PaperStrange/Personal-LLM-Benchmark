import { NgModule } from '@angular/core';
import { NbCardModule, NbIconModule } from '@nebular/theme';

import { ThemeModule } from '../../@theme/theme.module';
import { GatesComponent } from './gates.component';
import { GatesRoutingModule } from './gates-routing.module';

@NgModule({
  imports: [
    ThemeModule,
    NbCardModule,
    NbIconModule,
    GatesRoutingModule,
  ],
  declarations: [
    GatesComponent,
  ],
})
export class GatesModule { }
