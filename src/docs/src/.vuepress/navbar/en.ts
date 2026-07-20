import { navbar } from 'vuepress-theme-hope'

export const enNavbar = navbar([
  '/en/',
  '/en/guide/get-started',
  {
    text: 'Downloads',
    link: '/en/downloads',
    icon: 'download'
  },
  {
    text: 'Contact',
    link: '/en/contact-us',
    icon: 'message'
  },
  {
    text: 'Sponsor',
    link: '/en/sponsor',
    icon: 'thumbs-up'
  }
])
