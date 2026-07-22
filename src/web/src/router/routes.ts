import type { ExtendedRouteRecordRaw } from './types'

const NormalLayout = () => import('../layouts/normalLayout/normalLayout.vue')
const SinglePageLayout = () => import('../layouts/singlePageLayout/singlePageLayout.vue')

/**
 * 使用说明
 * 1- name 应与组件名一样，在 setup 中与文件名一样，才会有缓存
 * 2- noCache: true 不缓存
 */

// 根据权限显示的 routes
export const dynamicRoutes: ExtendedRouteRecordRaw[] = [
  {
    name: 'IndexHome',
    path: '/',
    component: NormalLayout,
    meta: {
      label: 'dashboardPage.index',
      icon: 'terminal',
      noCache: true,
      noMenu: true
    },
    redirect: '/calc-report/list',
    children: []
  },
  {
    name: 'User',
    path: '/user',
    component: NormalLayout,
    meta: {
      label: 'userPage.userInfo',
      icon: 'person',
      noTag: true,
      noMenu: true
    },
    redirect: '/user/profile',
    children: [
      {
        name: 'profileIndex',
        path: 'profile',
        meta: {
          icon: 'menu',
          label: 'userPage.profile'
        },
        component: () => import('pages/user/profileIndex.vue')
      }
    ]
  },
  {
    name: 'CalcReport',
    path: '/calc-report',
    component: NormalLayout,
    meta: {
      label: 'calcReportPage.calcManagement',
      icon: 'article'
    },
    redirect: '/calc-report/list',
    children: [
      {
        name: 'CalcReportList',
        path: 'list',
        meta: {
          icon: 'assignment',
          label: 'calcReportPage.calcReport',
          noCache: true
        },
        component: () => import('pages/calcReport/list/CalcReportList.vue')
      },
      {
        name: 'CalcReportNew',
        path: 'new',
        meta: {
          icon: 'add_box',
          label: 'calcReportPage.editCalcReport',
          noMenu: true
        },
        component: () => import('pages/calcReport/workbench/CalcReportWorkbench.vue')
      },
      {
        name: 'CalcReportWorkspace',
        path: ':reportOid/workspace',
        meta: { icon: 'code', label: 'calcWorkspace.workspace', noMenu: true, noCache: true },
        component: () => import('pages/calcReport/workbench/CalcReportWorkbench.vue')
      },
      {
        name: 'CalcReportRun',
        path: ':reportOid/run',
        meta: { icon: 'play_circle', label: 'calcWorkspace.run', noMenu: true, noCache: true },
        component: () => import('pages/calcExecution/CalcReportRun.vue')
      },
      {
        name: 'CalcReportVersions',
        path: ':reportOid/versions',
        meta: { icon: 'history', label: 'calcWorkspace.versions', noMenu: true, noCache: true },
        component: () => import('pages/calcReport/version/CalcReportVersions.vue')
      }
    ]
  },
  {
    name: 'CalcReportInstanceManagement',
    path: '/calc-report-instance',
    component: NormalLayout,
    meta: {
      label: 'calcReportInstancePage.calcsManagement',
      icon: 'article'
    },
    redirect: '/calc-report-instance/list',
    children: [
      {
        name: 'CalcReportInstanceList',
        path: 'list',
        meta: {
          icon: 'list_alt',
          label: 'calcReportInstancePage.myCalcs',
          noCache: true
        },
        component: () => import('pages/calcReportInstance/list/InstanceList.vue')
      },
      {
        name: 'CalcReportInstanceDetail',
        path: ':instanceOid',
        meta: {
          icon: 'description',
          label: 'calcWorkspace.instanceDetail',
          noMenu: true,
          noCache: true
        },
        component: () => import('pages/calcReportInstance/InstanceDetail.vue')
      }
    ]
  },
  // {
  //   name: 'CalcModule',
  //   path: '/calc-module',
  //   component: NormalLayout,
  //   meta: {
  //     label: 'calcModulePage.calcModule',
  //     icon: 'calculate'
  //   },
  //   redirect: '/calc-module/list',
  //   children: [
  //     {
  //       name: 'calcModuleList',
  //       path: 'list',
  //       meta: {
  //         icon: 'calculate',
  //         label: 'calcModulePage.calcModule'
  //       },
  //       component: () => import('pages/calcModule/CalcModuleList.vue')
  //     }
  //   ]
  // },
  {
    name: 'UserManagement',
    path: '/user-management',
    component: NormalLayout,
    meta: {
      label: 'userManagement.title',
      icon: 'manage_accounts',
      access: ['admin'],
      denies: ['desktop-api']
    },
    redirect: '/user-management/index',
    children: [
      {
        name: 'UserManagementIndex',
        path: 'index',
        meta: { label: 'userManagement.title', icon: 'manage_accounts', noCache: true },
        component: () => import('pages/userManagement/UserManagementIndex.vue')
      }
    ]
  },
  {
    name: 'Sponsor',
    path: '/sponsor',
    component: NormalLayout,
    meta: {
      label: 'routes.sponsorAuthor',
      icon: 'thumb_up',
      denies: ['professional', 'enterprise']
    },
    redirect: '/sponsor/author',
    children: [
      {
        name: 'SponsorAuthor',
        path: 'author',
        meta: {
          icon: 'thumb_up',
          label: 'routes.sponsorAuthor',
          noTag: true
        },
        component: () => import('pages/sponsor/sponsorAuthor.vue')
      }
    ]
  },
  {
    name: 'Help',
    path: '/help',
    component: NormalLayout,
    meta: {
      label: 'routes.helpDoc',
      icon: 'settings_suggest'
    },
    redirect: '/help/start-guide',
    children: [
      {
        name: 'StartGuide',
        path: 'start-guide',
        component: () => import('pages/help/StartGuide.vue'),
        meta: {
          icon: 'help',
          label: 'routes.startGuide',
          noTag: true
        }
      }
    ]
  }
]

// 静态 routes
export const constantRoutes: ExtendedRouteRecordRaw[] = [
  {
    name: 'PublicShares',
    path: '/public',
    component: SinglePageLayout,
    meta: { label: 'calcWorkspace.sharedReport', icon: 'share', noMenu: true, anonymous: true },
    children: [
      {
        name: 'CalcReportSharedImport',
        path: '/calc-report/shared/import',
        meta: {
          label: 'calcWorkspace.importSharedReport',
          icon: 'download',
          noMenu: true,
          noCache: true,
          anonymous: true
        },
        component: () => import('pages/calcReport/shared/SharedImport.vue')
      },
      {
        name: 'CalcReportInstanceShared',
        path: '/calc-report-instance/shared/:token',
        meta: {
          label: 'calcWorkspace.sharedInstance',
          icon: 'share',
          noMenu: true,
          noCache: true,
          anonymous: true
        },
        component: () => import('pages/calcReportInstance/SharedInstanceDetail.vue')
      }
    ]
  },
  {
    name: 'Login',
    path: '/login',
    component: () => import('src/pages/login/loginIndex.vue'),
    meta: {
      label: 'routes.login',
      icon: 'login',
      noMenu: true, // 在菜单中隐藏
      noTag: true // 在标签中隐藏
    }
  }
  // {
  //   name: 'SinglePages',
  //   path: '/pages',
  //   component: SinglePageLayout,
  //   meta: {
  //     label: 'singlePages',
  //     icon: 'view_carousel',
  //     noMenu: true,
  //     noTag: true
  //   },
  //   children: [
  //   ]
  // }
]

// 放到最后添加
export const exceptionRoutes: ExtendedRouteRecordRaw[] = [
  // Always leave this as last one,
  // but you can also remove it
  // 异常处理
  {
    name: 'exception',
    path: '/:catchAll(.*)*',
    meta: {
      label: 'routes.exception',
      icon: 'error',
      noMenu: true, // 在菜单中隐藏
      noTag: true // 在标签中隐藏
    },
    component: () => import('pages/ErrorNotFound.vue')
  }
]
