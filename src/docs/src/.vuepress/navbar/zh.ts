import { navbar } from 'vuepress-theme-hope'

export const zhNavbar = navbar([
  '/',
  '/guide/get-started',
  {
    text: '软件下载',
    link: '/downloads',
    icon: 'download'
  },
  {
    text: '联系我们',
    link: '/contact-us',
    icon: 'message'
  },
  {
    text: '赞助支持',
    link: '/sponsor',
    icon: 'thumbs-up'
  }
])
