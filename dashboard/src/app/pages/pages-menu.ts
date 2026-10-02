import { NbMenuItem } from '@nebular/theme';

export const MENU_ITEMS: NbMenuItem[] = [
  {
    title: 'Overview',
    icon: 'home-outline',
    link: '/pages/dashboard',
    home: true,
  },
  {
    title: 'BENCHMARK',
    group: true,
  },
  {
    title: 'Gates',
    icon: 'shield-outline',
    link: '/pages/gates',
  },
  {
    title: 'Results',
    icon: 'bar-chart-outline',
    link: '/pages/results',
  },
];
