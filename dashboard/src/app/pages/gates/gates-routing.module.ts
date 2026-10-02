import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { GatesComponent } from './gates.component';

const routes: Routes = [{
  path: '',
  component: GatesComponent,
}];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class GatesRoutingModule { }
