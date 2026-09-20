import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '系统架构设计师',
  titleTemplate: '软考学习笔记',
  description: '软考高级系统架构设计师学习笔记',
  lastUpdated: true,
  lang: 'zh-CN',
  cleanUrls: true,
  markdown: {
    math: true
  },

  themeConfig: {
    outline: {
      label: '本页目录',
      level: [2, 3]
    },
    docFooter: {
      prev: '上一页',
      next: '下一页'
    },
    lastUpdatedText: '最后更新',
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',

    nav: [
      { text: '首页', link: '/' },
      { text: '笔记', link: '/notes/chapter-01/' },
      { text: '课件原文', link: '/source/chapter-01/' },
      { text: '教材原文', link: '/textbook/' },
      { text: '关于', link: '/guide/introduction' }
    ],

    sidebar: {
      '/notes/': [
        {
          text: '学习笔记',
          items: [
            { text: '第一章 计算机系统基础知识', link: '/notes/chapter-01/' },
            { text: '第二章 操作系统知识', link: '/notes/chapter-02/' },
            { text: '第三章 数据库', link: '/notes/chapter-03/' },
            { text: '第四章 嵌入式', link: '/notes/chapter-04/' },
            { text: '第五章 计算机网络', link: '/notes/chapter-05/' },
            { text: '第六章 其他计算机系统基础知识', link: '/notes/chapter-06/' },
            { text: '第七章 系统性能', link: '/notes/chapter-07/' },
            { text: '第八章 信息系统基础知识', link: '/notes/chapter-08/' },
            { text: '第九章 系统安全', link: '/notes/chapter-09/' },
            { text: '第十章 软件工程基础知识', link: '/notes/chapter-10/' },
            { text: '第十一章 面向对象技术', link: '/notes/chapter-11/' },
            { text: '第十二章 项目管理', link: '/notes/chapter-12/' },
            { text: '第十三章 系统架构设计', link: '/notes/chapter-13/' },
            { text: '第十四章 软件可靠性基础知识', link: '/notes/chapter-14/' },
            { text: '第十五章 软件架构的演化和维护', link: '/notes/chapter-15/' },
            { text: '第十六章 未来信息综合技术', link: '/notes/chapter-16/' },
            { text: '第十七章 补充：知识产权', link: '/notes/chapter-17/' },
            { text: '第十八章 补充：数学与经济管理', link: '/notes/chapter-18/' }
          ]
        }
      ],
      '/source/': [
        {
          text: '课件原文',
          items: [
            { text: '第一章 计算机系统基础知识', link: '/source/chapter-01/' },
            { text: '第二章 操作系统知识', link: '/source/chapter-02/' },
            { text: '第三章 数据库', link: '/source/chapter-03/' },
            { text: '第四章 嵌入式', link: '/source/chapter-04/' },
            { text: '第五章 计算机网络', link: '/source/chapter-05/' },
            { text: '第六章 其他计算机系统基础知识', link: '/source/chapter-06/' },
            { text: '第七章 系统性能', link: '/source/chapter-07/' },
            { text: '第八章 信息系统基础知识', link: '/source/chapter-08/' },
            { text: '第九章 系统安全', link: '/source/chapter-09/' },
            { text: '第十章 软件工程基础知识', link: '/source/chapter-10/' },
            { text: '第十一章 面向对象技术', link: '/source/chapter-11/' },
            { text: '第十二章 项目管理', link: '/source/chapter-12/' },
            { text: '第十三章 系统架构设计', link: '/source/chapter-13/' },
            { text: '第十四章 软件可靠性基础知识', link: '/source/chapter-14/' },
            { text: '第十五章 软件架构的演化和维护', link: '/source/chapter-15/' },
            { text: '第十六章 未来信息综合技术', link: '/source/chapter-16/' },
            { text: '第十七章 补充：知识产权', link: '/source/chapter-17/' },
            { text: '第十八章 补充：数学与经济管理', link: '/source/chapter-18/' }
          ]
        }
      ],

      '/textbook/': [
        {
          text: '教材原文',
          items: [
            { text: '前置内容', link: '/textbook/' },
            { text: '第 1 章 绪论', link: '/textbook/chapter-01/' },
            { text: '第 2 章 计算机系统基础知识', link: '/textbook/chapter-02/' },
            { text: '第 3 章 信息系统基础知识', link: '/textbook/chapter-03/' },
            { text: '第 4 章 信息安全技术基础知识', link: '/textbook/chapter-04/' },
            { text: '第 5 章 软件工程基础知识', link: '/textbook/chapter-05/' },
            { text: '第 6 章 数据库设计基础知识', link: '/textbook/chapter-06/' },
            { text: '第 7 章 系统架构设计基础知识', link: '/textbook/chapter-07/' },
            { text: '第 8 章 系统质量属性与架构评估', link: '/textbook/chapter-08/' },
            { text: '第 9 章 软件可靠性基础知识', link: '/textbook/chapter-09/' },
            { text: '第 10 章 软件架构的演化和维护', link: '/textbook/chapter-10/' },
            { text: '第 11 章 未来信息综合技术', link: '/textbook/chapter-11/' },
            { text: '第 12 章 信息系统架构设计理论与实践', link: '/textbook/chapter-12/' },
            { text: '第 13 章 层次式架构设计理论与实践', link: '/textbook/chapter-13/' },
            { text: '第 14 章 云原生架构设计理论与实践', link: '/textbook/chapter-14/' },
            { text: '第 15 章 面向服务架构设计理论与实践', link: '/textbook/chapter-15/' },
            { text: '第 16 章 嵌入式系统架构设计理论与实践', link: '/textbook/chapter-16/' },
            { text: '第 17 章 通信系统架构设计理论与实践', link: '/textbook/chapter-17/' },
            { text: '第 18 章 安全架构设计理论与实践', link: '/textbook/chapter-18/' },
            { text: '第 19 章 大数据架构设计理论与实践', link: '/textbook/chapter-19/' },
            { text: '第 20 章 论文写作要点', link: '/textbook/chapter-20/' }
          ]
        }
      ],

      '/guide/': [
        {
          text: '指南',
          items: [
            { text: '项目介绍', link: '/guide/introduction' },
            { text: '使用说明', link: '/guide/usage' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/' }
    ],

    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档'
          },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换'
            }
          }
        }
      }
    }
  }
})
