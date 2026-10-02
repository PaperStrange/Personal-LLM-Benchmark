import { Component } from '@angular/core';
import { NbMenuService } from '@nebular/theme';
import { Router } from '@angular/router';

@Component({
  selector: 'ngx-not-found',
  template: `
    <div class="row">
      <div class="col-md-12">
        <nb-card>
          <nb-card-body>
            <div class="flex-centered col-xl-4 col-lg-6 col-md-8 col-sm-12">
              <h2 class="title">404 Page Not Found</h2>
              <button nbButton status="primary" (click)="goToHome()" class="home-button">
                Take me home
              </button>
            </div>
          </nb-card-body>
        </nb-card>
      </div>
    </div>
  `,
})
export class NotFoundComponent {
  constructor(private menuService: NbMenuService, private router: Router) {}

  goToHome() {
    this.menuService.navigateHome();
  }
}
