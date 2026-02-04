// 简体中文
export default {
  // 通用
  common: {
    appName: 'BaiduIndexHunter',
    version: 'v2.0',
    save: '保存',
    cancel: '取消',
    confirm: '确认',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    refresh: '刷新',
    search: '搜索',
    filter: '筛选',
    reset: '重置',
    loading: '加载中...',
    success: '成功',
    error: '错误',
    warning: '警告',
    info: '提示',
    noData: '暂无数据',
    total: '共',
    items: '条',
    page: '页',
    actions: '操作',
    status: '状态',
    createTime: '创建时间',
    updateTime: '更新时间',
    learningProject: '学习项目',
  },

  // 导航菜单
  nav: {
    home: '首页',
    dataCollection: '数据采集',
    cookieManager: 'Cookie管理',
    dashboard: '数据大屏',
    settings: '配置信息',
    about: '关于项目',
    privacy: '隐私政策',
  },

  // 页脚
  footer: {
    disclaimer: '本项目仅供个人学习交流使用，严禁用于商业用途。使用本项目产生的一切责任由使用者自行承担。',
    copyright: '© {year} BaiduIndexHunter - 学习项目',
    aboutProject: '关于项目',
    privacyPolicy: '隐私政策',
  },

  // 首页
  home: {
    title: '百度指数数据采集系统',
    subtitle: '高效、稳定的百度指数数据采集工具',
    startNow: '开始采集',
    learnMore: '了解更多',
    featuresTitle: '核心特性',
    workflowTitle: '使用流程',
    features: {
      efficient: {
        title: '高效爬取',
        desc: '优化的爬取策略，智能管理Cookie，确保爬取效率和成功率',
      },
      multiData: {
        title: '多维度数据',
        desc: '支持搜索指数、媒体指数等多维度数据采集，满足不同研究需求',
      },
      timeDimension: {
        title: '丰富的时间维度',
        desc: '支持日度、周度数据，可灵活选择时间范围和对比时间',
      },
      multiTerminal: {
        title: '多终端支持',
        desc: '区分PC和移动端数据，全面了解用户行为特征',
      },
      smartExport: {
        title: '智能导出',
        desc: '支持Excel、CSV等多种格式导出，数据处理更便捷',
      },
      stable: {
        title: '稳定可靠',
        desc: '智能Cookie池管理，保障长时间稳定采集',
      },
    },
    workflow: {
      step1: { title: '选择关键词', desc: '输入关键词或上传文件' },
      step2: { title: '选择时间范围', desc: '自定义采集的时间范围' },
      step3: { title: '选择城市', desc: '全国或特定城市数据' },
      step4: { title: '选择数据类型', desc: '搜索指数、媒体指数等' },
      step5: { title: '开始采集', desc: '一键获取所需数据' },
    },
    cta: {
      title: '开始学习数据采集技术',
      description: '本项目帮助您学习爬虫技术、任务调度、数据可视化等多方面技能。',
      button: '立即开始',
    },
  },

  // 数据采集页
  dataCollection: {
    title: '百度指数数据采集',
    apiStatus: 'API状态',
    connected: '服务运行中',
    disconnected: '服务未连接',
    status: {
      running: '服务运行中',
      disconnected: '服务未连接',
    },
    tabs: {
      searchIndex: '搜索指数',
      feedIndex: '资讯指数',
      wordGraph: '需求图谱',
      demographicAttributes: '人群属性',
      interestProfile: '兴趣分析',
      regionDistribution: '地域分布',
      taskList: '任务列表',
    },
    dialog: {
      title: 'API服务状态',
      normal: 'API服务正常',
      abnormal: 'API服务异常',
      normalDesc: '服务连接正常，可以正常采集数据',
      abnormalDesc: '无法连接到API服务，请确保后端服务已启动',
      apiAddress: 'API地址',
    },
    progress: {
      currentTask: '当前任务',
      progress: '进度',
      running: '正在执行...',
    },
    taskTypes: {
      searchIndex: '搜索指数',
      feedIndex: '资讯指数',
      wordGraph: '需求图谱',
      demographic: '人群属性',
      interest: '兴趣分布',
      region: '地域分布',
    },
    form: {
      keywords: '关键词',
      keywordsPlaceholder: '请输入关键词，多个关键词用逗号分隔',
      dateRange: '时间范围',
      region: '地域',
      allRegion: '全国',
      priority: '优先级',
      submit: '创建任务',
    },
  },

  // Cookie管理页
  cookieManager: {
    title: 'Cookie 管理',
    stats: {
      total: '总数',
      available: '可用',
      tempBanned: '临时封禁',
      permBanned: '永久封禁',
    },
    actions: {
      testAll: '测试全部可用性',
      updateStatus: '更新Cookie状态',
      cleanExpired: '清理过期Cookie',
      syncRedis: '同步到Redis',
      updateAbSr: '更新ab_sr',
      batchBan: '批量封禁所有Cookie',
      batchUnban: '批量解封所有Cookie',
    },
    table: {
      name: 'Cookie名',
      fieldCount: '字段数量',
      value: 'Cookie值',
      status: '状态',
      expireTime: '过期时间',
      neverExpire: '永不过期',
    },
    status: {
      available: '可用',
      tempBanned: '临时封禁',
      permBanned: '永久封禁',
      expired: '已过期',
    },
  },

  // 数据大屏
  dashboard: {
    title: '百度指数爬虫数据大屏',
    selectTaskType: '选择任务类型',
    selectPeriod: '统计周期',
    allStats: '全部统计',
    periods: {
      last24h: '最近24小时',
      last3d: '最近3天',
      last7d: '最近7天',
      last30d: '最近30天',
      last90d: '最近90天',
      last180d: '最近半年',
      last365d: '最近一年',
      allTime: '全部时间',
      custom: '自定义时间范围',
    },
    stats: {
      totalTasks: '总任务数',
      completedTasks: '完成任务',
      failedTasks: '失败任务',
      totalItems: '数据总量',
      crawledItems: '爬取条数',
      successRate: '成功率',
      avgDuration: '平均耗时',
    },
    charts: {
      taskTrend: '任务执行趋势',
      dataTrend: '数据爬取趋势',
      successRate: '任务成功率对比',
      avgDuration: '平均执行时间对比',
      dataVolume: '数据爬取量对比',
    },
  },

  // 设置页
  settings: {
    title: '系统配置',
    groups: {
      task: '任务配置',
      spider: '爬虫配置',
      cookie: 'Cookie配置',
      output: '输出配置',
      ui: '界面设置',
    },
    ui: {
      theme: '界面主题',
      themeLight: '浅色模式',
      themeDark: '深色模式',
      language: '界面语言',
      languageTip: '选择界面显示语言，部分内容需刷新页面后生效',
      themeTip: '选择界面显示主题，立即生效',
      localStorageNote: '界面设置保存在本地浏览器中，不会同步到服务器。',
    },
    configs: {
      'task.max_concurrent_tasks': '最大并发任务数',
      'task.queue_check_interval': '任务队列检查间隔（秒）',
      'task.default_priority': '默认任务优先级（1-10）',
      'task.max_retry_count': '任务最大重试次数',
      'task.retry_delay': '任务重试延迟（秒）',
      'spider.min_interval': '请求间隔最小秒数',
      'spider.max_interval': '请求间隔最大秒数',
      'spider.retry_times': '请求失败重试次数',
      'spider.timeout': '请求超时时间（秒）',
      'spider.max_workers': '最大工作线程数',
      'spider.user_agent_rotation': '是否轮换User-Agent',
      'spider.proxy_enabled': '是否启用代理',
      'spider.proxy_url': '代理URL',
      'spider.failure_multiplier': '失败后间隔倍数',
      'output.default_format': '默认输出格式',
      'output.csv_encoding': 'CSV文件编码',
      'output.excel_sheet_name': 'Excel工作表名称',
      'output.file_name_template': '文件名模板',
      'cookie.block_cooldown': 'Cookie封禁冷却时间（秒）',
      'cookie.max_usage_per_day': '每日最大使用次数',
      'cookie.min_available_count': '最小可用Cookie数量',
      'cookie.rotation_strategy': 'Cookie轮换策略',
    },
    actions: {
      save: '保存配置',
      reset: '重置为默认配置',
    },
    messages: {
      saveSuccess: '配置保存成功',
      resetSuccess: '配置已重置为默认值',
    },
  },

  // 关于页
  about: {
    title: '关于 BaiduIndexHunter',
    subtitle: '一个用于学习的百度指数数据采集与分析工具',
    disclaimer: {
      title: '重要声明',
      content1: '本项目仅供个人学习和技术研究使用，严禁用于任何商业用途。',
      content2: '如果您将本项目用于商业目的或造成任何损失，由此产生的一切法律责任和后果由使用者自行承担，与项目作者无关。使用本项目即表示您已阅读并同意此声明。',
    },
    intro: {
      title: '项目介绍',
      p1: 'BaiduIndexHunter是一个用于学习的个人项目，旨在帮助开发者学习和研究网络爬虫技术、数据采集与分析方法。',
      p2: '通过本项目，您可以学习到：Cookie管理机制、任务调度系统设计、分布式架构思想、数据可视化展示等多方面的技术知识。',
      p3: '本项目采用 Vue 3 + Flask + Scrapy 技术栈，代码结构清晰，注释完善，适合作为学习参考。',
    },
    features: {
      title: '技术特点',
      scrapy: {
        title: 'Scrapy 框架',
        desc: '采用 Scrapy 框架进行数据采集，支持断点续传、安全退出、灵活的中间件配置等特性。',
      },
      scheduler: {
        title: '任务调度系统',
        desc: '支持多任务并发执行，智能负载均衡，任务队列管理，实时状态监控。',
      },
      dataTypes: {
        title: '全面的数据类型',
        desc: '支持搜索指数、资讯指数、需求图谱、人群画像、地域分布、兴趣分布等多种数据类型的采集。',
      },
      resume: {
        title: '断点续传机制',
        desc: '采集过程中如遇异常中断，系统自动保存进度，重启后可从断点继续，避免重复工作。',
      },
    },
    coreFeatures: {
      title: '核心特性',
      efficient: {
        title: '高效爬取',
        desc: '智能Cookie管理和负载均衡，确保稳定可靠的数据获取',
      },
      multiData: {
        title: '多维数据',
        desc: '支持搜索指数、媒体指数、需求图谱等多种数据类型',
      },
      easyUse: {
        title: '易于使用',
        desc: '直观的用户界面，简化复杂操作，快速获取所需数据',
      },
      export: {
        title: '灵活导出',
        desc: '支持多种格式导出，便于进一步分析和处理',
      },
      monitor: {
        title: '实时监控',
        desc: '实时监控任务执行状态，及时发现和处理异常情况',
      },
      trend: {
        title: '趋势分析',
        desc: '内置趋势分析工具，帮助您洞察市场动态和用户需求',
      },
    },
    techStack: {
      title: '技术架构',
      frontend: '前端技术',
      backend: '后端技术',
      dataProcess: '数据处理',
    },
    faq: {
      title: '常见问题',
      q1: 'BaiduIndexHunter是什么？',
      a1: 'BaiduIndexHunter是一个用于学习和研究的百度指数数据采集工具，帮助您了解关键词搜索趋势、地域分布等数据分析方法。本项目仅供个人学习交流使用。',
      q2: '如何开始使用？',
      a2: '首先在配置页面设置您的数据库和Redis连接信息，然后添加您的百度账号Cookie，最后在数据采集页面输入关键词、选择时间范围和地域即可开始获取数据。',
      q3: '数据采集需要多长时间？',
      a3: '采集时间取决于关键词数量、时间范围和选择的地域数量。系统采用智能爬取策略，通常每个请求间隔0.1-0.3秒。大量数据采集建议使用任务调度功能。',
      q4: '支持哪些数据导出格式？',
      a4: '当前支持CSV、Excel、JSON格式导出。导出的数据包含完整的时间序列信息，可直接导入Excel或其他数据分析工具进行深度分析。',
      q5: '如何保证数据采集的稳定性？',
      a5: '系统内置Cookie池管理机制，支持多账号轮换使用；采用智能限流策略，避免触发反爬机制；提供任务断点续传功能，异常中断后可自动恢复。',
      q6: '这个项目可以用于商业用途吗？',
      a6: '不可以。本项目仅供个人学习和技术研究使用，严禁用于任何商业用途。如果您将本项目用于商业目的，由此产生的一切法律责任和后果由使用者自行承担。',
    },
    projectInfo: {
      title: '项目信息',
      personalProject: {
        title: '个人项目',
        desc: '本项目为个人学习项目，仅供学习交流使用，不对外提供任何服务。',
      },
      disclaimer: {
        title: '免责声明',
        desc: '本项目仅供学习研究使用，严禁商业用途。使用者需自行承担使用本项目产生的一切责任。',
      },
      techLearning: {
        title: '技术学习',
        desc: '通过本项目您可以学习到爬虫技术、任务调度、数据可视化等多方面的开发技能。',
      },
      localUse: {
        title: '本地使用',
        desc: '本项目设计为本地运行使用，不涉及服务器部署和对外提供服务。',
      },
    },
  },

  // 隐私政策页
  privacy: {
    title: '隐私政策与免责声明',
    lastUpdated: '最后更新',
    disclaimer: {
      title: '重要声明',
      content: '本项目仅供个人学习和技术研究使用，严禁用于任何商业用途。如果您将本项目用于商业目的或造成任何损失，由此产生的一切法律责任和后果由使用者自行承担，与项目作者无关。',
    },
    sections: {
      projectNature: {
        title: '项目性质',
        intro: 'BaiduIndexHunter 是一个个人学习项目，旨在帮助开发者学习和研究网络爬虫技术、数据采集与分析方法。本项目：',
        items: [
          '仅供学习交流：本项目仅用于技术学习和研究目的',
          '本地运行：设计为在本地计算机上运行，不涉及对外提供服务',
          '非商业用途：严禁将本项目用于任何商业目的',
          '风险自负：使用本项目产生的任何后果由使用者自行承担',
        ],
      },
      dataNote: {
        title: '数据说明',
        intro: '由于本项目设计为本地运行，所有数据均存储在您的本地计算机上：',
        items: [
          '本地存储：所有配置信息、Cookie数据、采集结果均存储在本地数据库',
          '无远程传输：本项目不会将您的数据传输到任何远程服务器',
          '用户自主管理：您对本地存储的所有数据拥有完全控制权',
        ],
      },
      cookieNote: {
        title: 'Cookie 使用说明',
        intro: '本项目需要您提供百度账号的 Cookie 信息来访问百度指数数据。请注意：',
        items: [
          'Cookie 信息仅存储在您的本地数据库中',
          '请勿将 Cookie 信息分享给他人',
          '定期更新 Cookie 以确保其有效性',
          '如果账号出现异常，请立即停止使用并更换 Cookie',
        ],
      },
      risks: {
        title: '使用风险',
        intro: '使用本项目可能存在以下风险，请您充分了解：',
        items: [
          '账号风险：频繁请求可能导致百度账号被限制或封禁',
          '法律风险：未经授权采集数据可能违反相关法律法规',
          '数据准确性：采集的数据仅供参考，不保证其准确性和完整性',
        ],
        note: '您在使用本项目前应充分了解并评估上述风险，使用本项目即表示您已接受这些风险。',
      },
      disclaimerTerms: {
        title: '免责条款',
        items: [
          '本项目按"原样"提供，不提供任何形式的明示或暗示保证',
          '项目作者不对使用本项目造成的任何直接或间接损失负责',
          '项目作者不对数据的准确性、完整性或可用性做任何保证',
          '使用本项目导致的任何法律问题由使用者自行承担',
          '本项目可能随时停止维护，恕不另行通知',
        ],
      },
      compliance: {
        title: '合规使用',
        intro: '请您在使用本项目时遵守以下原则：',
        items: [
          '遵守中华人民共和国相关法律法规',
          '遵守百度指数的使用条款和服务协议',
          '合理控制请求频率，避免对目标服务器造成负担',
          '仅将采集的数据用于个人学习和研究',
          '不得将采集的数据用于任何商业用途',
        ],
      },
      contact: {
        title: '联系方式',
        content: '如果您对本隐私政策有任何疑问，请通过项目相关渠道联系作者。',
      },
    },
  },
}
