// English
export default {
  // Common
  common: {
    appName: 'BaiduIndexHunter',
    version: 'v2.0',
    save: 'Save',
    cancel: 'Cancel',
    confirm: 'Confirm',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    refresh: 'Refresh',
    search: 'Search',
    filter: 'Filter',
    reset: 'Reset',
    loading: 'Loading...',
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info',
    noData: 'No Data',
    total: 'Total',
    items: 'items',
    page: 'page',
    actions: 'Actions',
    status: 'Status',
    createTime: 'Created At',
    updateTime: 'Updated At',
    learningProject: 'Learning Project',
  },

  // Navigation
  nav: {
    home: 'Home',
    dataCollection: 'Data Collection',
    cookieManager: 'Cookie Manager',
    dashboard: 'Dashboard',
    settings: 'Settings',
    about: 'About',
    privacy: 'Privacy',
  },

  // Footer
  footer: {
    disclaimer: 'This project is for personal learning only. Commercial use is strictly prohibited. Users bear all responsibilities.',
    copyright: '© {year} BaiduIndexHunter - Learning Project',
    aboutProject: 'About',
    privacyPolicy: 'Privacy Policy',
  },

  // Home
  home: {
    title: 'Baidu Index Data Collection System',
    subtitle: 'Efficient and stable Baidu Index data collection tool',
    startNow: 'Start Collection',
    learnMore: 'Learn More',
    featuresTitle: 'Core Features',
    workflowTitle: 'Workflow',
    features: {
      efficient: {
        title: 'Efficient Crawling',
        desc: 'Optimized crawling strategy with smart Cookie management for high efficiency',
      },
      multiData: {
        title: 'Multi-dimensional Data',
        desc: 'Support search index, media index and more data types for various research needs',
      },
      timeDimension: {
        title: 'Flexible Time Range',
        desc: 'Support daily and weekly data with customizable time range',
      },
      multiTerminal: {
        title: 'Multi-terminal Support',
        desc: 'Distinguish PC and mobile data for comprehensive user behavior analysis',
      },
      smartExport: {
        title: 'Smart Export',
        desc: 'Support Excel, CSV and other formats for convenient data processing',
      },
      stable: {
        title: 'Stable & Reliable',
        desc: 'Smart Cookie pool management for long-term stable collection',
      },
    },
    workflow: {
      step1: { title: 'Select Keywords', desc: 'Input keywords or upload file' },
      step2: { title: 'Select Time Range', desc: 'Customize collection period' },
      step3: { title: 'Select Region', desc: 'Nationwide or specific cities' },
      step4: { title: 'Select Data Type', desc: 'Search index, media index, etc.' },
      step5: { title: 'Start Collection', desc: 'One-click data retrieval' },
    },
    cta: {
      title: 'Start Learning Data Collection',
      description: 'This project helps you learn crawling, task scheduling, data visualization and more.',
      button: 'Get Started',
    },
  },

  // Data Collection
  dataCollection: {
    title: 'Baidu Index Data Collection',
    status: {
      running: 'Service Running',
      disconnected: 'Service Disconnected',
    },
    tabs: {
      searchIndex: 'Search Index',
      feedIndex: 'News Index',
      wordGraph: 'Demand Graph',
      demographicAttributes: 'Demographics',
      interestProfile: 'Interest Profile',
      regionDistribution: 'Region Distribution',
      taskList: 'Task List',
    },
    dialog: {
      title: 'API Service Status',
      normal: 'API Service Normal',
      abnormal: 'API Service Error',
      normalDesc: 'Connection successful, data collection available',
      abnormalDesc: 'Unable to connect to API, please ensure backend is running',
      apiAddress: 'API Address',
    },
    progress: {
      currentTask: 'Current Task',
      progress: 'Progress',
      running: 'Running...',
    },
    // Keep existing keys below
    title: 'Data Collection',
    apiStatus: 'API Status',
    connected: 'Service Running',
    disconnected: 'Service Disconnected',
    taskTypes: {
      searchIndex: 'Search Index',
      feedIndex: 'Feed Index',
      wordGraph: 'Word Graph',
      demographic: 'Demographics',
      interest: 'Interest',
      region: 'Region',
    },
    form: {
      keywords: 'Keywords',
      keywordsPlaceholder: 'Enter keywords, separated by commas',
      dateRange: 'Date Range',
      region: 'Region',
      allRegion: 'All Regions',
      priority: 'Priority',
      submit: 'Create Task',
    },
  },

  // Cookie Manager
  cookieManager: {
    title: 'Cookie Manager',
    stats: {
      total: 'Total',
      available: 'Available',
      tempBanned: 'Temp Banned',
      permBanned: 'Perm Banned',
    },
    actions: {
      testAll: 'Test All',
      updateStatus: 'Update Status',
      cleanExpired: 'Clean Expired',
      syncRedis: 'Sync to Redis',
      updateAbSr: 'Update ab_sr',
      batchBan: 'Ban All Cookies',
      batchUnban: 'Unban All Cookies',
    },
    table: {
      name: 'Cookie Name',
      fieldCount: 'Field Count',
      value: 'Cookie Value',
      status: 'Status',
      expireTime: 'Expire Time',
      neverExpire: 'Never Expire',
    },
    status: {
      available: 'Available',
      tempBanned: 'Temp Banned',
      permBanned: 'Perm Banned',
      expired: 'Expired',
    },
  },

  // Dashboard
  dashboard: {
    title: 'Baidu Index Crawler Dashboard',
    selectTaskType: 'Select Task Type',
    selectPeriod: 'Select Period',
    allStats: 'All Stats',
    periods: {
      last24h: 'Last 24 Hours',
      last3d: 'Last 3 Days',
      last7d: 'Last 7 Days',
      last30d: 'Last 30 Days',
      last90d: 'Last 90 Days',
      last180d: 'Last 6 Months',
      last365d: 'Last Year',
      allTime: 'All Time',
      custom: 'Custom Range',
    },
    stats: {
      totalTasks: 'Total Tasks',
      completedTasks: 'Completed',
      failedTasks: 'Failed',
      totalItems: 'Total Data',
      crawledItems: 'Crawled',
      successRate: 'Success Rate',
      avgDuration: 'Avg Duration',
    },
    charts: {
      taskTrend: 'Task Execution Trend',
      dataTrend: 'Data Crawling Trend',
      successRate: 'Success Rate Comparison',
      avgDuration: 'Avg Duration Comparison',
      dataVolume: 'Data Volume Comparison',
    },
  },

  // Settings
  settings: {
    title: 'System Settings',
    groups: {
      task: 'Task Settings',
      spider: 'Spider Settings',
      cookie: 'Cookie Settings',
      output: 'Output Settings',
      ui: 'UI Settings',
    },
    ui: {
      theme: 'Theme',
      themeLight: 'Light Mode',
      themeDark: 'Dark Mode',
      language: 'Language',
      languageTip: 'Select display language. Some content requires page refresh.',
      themeTip: 'Select display theme. Takes effect immediately.',
      localStorageNote: 'UI settings are saved in local browser storage and will not sync to server.',
    },
    configs: {
      'task.max_concurrent_tasks': 'Max Concurrent Tasks',
      'task.queue_check_interval': 'Queue Check Interval (s)',
      'task.default_priority': 'Default Priority (1-10)',
      'task.max_retry_count': 'Max Retry Count',
      'task.retry_delay': 'Retry Delay (s)',
      'spider.min_interval': 'Min Request Interval (s)',
      'spider.max_interval': 'Max Request Interval (s)',
      'spider.retry_times': 'Request Retry Times',
      'spider.timeout': 'Request Timeout (s)',
      'spider.max_workers': 'Max Workers',
      'spider.user_agent_rotation': 'Rotate User-Agent',
      'spider.proxy_enabled': 'Enable Proxy',
      'spider.proxy_url': 'Proxy URL',
      'spider.failure_multiplier': 'Failure Interval Multiplier',
      'output.default_format': 'Default Output Format',
      'output.csv_encoding': 'CSV Encoding',
      'output.excel_sheet_name': 'Excel Sheet Name',
      'output.file_name_template': 'File Name Template',
      'cookie.block_cooldown': 'Cookie Block Cooldown (s)',
      'cookie.max_usage_per_day': 'Max Usage Per Day',
      'cookie.min_available_count': 'Min Available Count',
      'cookie.rotation_strategy': 'Rotation Strategy',
    },
    actions: {
      save: 'Save Settings',
      reset: 'Reset to Default',
    },
    messages: {
      saveSuccess: 'Settings saved successfully',
      resetSuccess: 'Settings reset to default',
    },
  },

  // About
  about: {
    title: 'About BaiduIndexHunter',
    subtitle: 'A Baidu Index data collection tool for learning',
    disclaimer: {
      title: 'Important Notice',
      content1: 'This project is for personal learning and research only. Commercial use is strictly prohibited.',
      content2: 'If you use this project for commercial purposes or cause any damage, all legal responsibilities and consequences are borne by the user. By using this project, you agree to this statement.',
    },
    intro: {
      title: 'Introduction',
      p1: 'BaiduIndexHunter is a personal learning project designed to help developers learn web crawling, data collection, and analysis techniques.',
      p2: 'Through this project, you can learn: Cookie management, task scheduling system design, distributed architecture concepts, data visualization, and more.',
      p3: 'Built with Vue 3 + Flask + Scrapy stack, with clear code structure and comprehensive comments, suitable for learning reference.',
    },
    features: {
      title: 'Technical Features',
      scrapy: {
        title: 'Scrapy Framework',
        desc: 'Uses Scrapy for data collection with breakpoint resume, safe exit, and flexible middleware configuration.',
      },
      scheduler: {
        title: 'Task Scheduler',
        desc: 'Supports concurrent task execution, smart load balancing, queue management, and real-time monitoring.',
      },
      dataTypes: {
        title: 'Comprehensive Data Types',
        desc: 'Supports search index, feed index, word graph, demographics, region, and interest distribution.',
      },
      resume: {
        title: 'Breakpoint Resume',
        desc: 'Auto saves progress on interruption, resumes from breakpoint after restart to avoid duplicate work.',
      },
    },
    coreFeatures: {
      title: 'Core Features',
      efficient: {
        title: 'Efficient Crawling',
        desc: 'Smart Cookie management and load balancing for stable data collection',
      },
      multiData: {
        title: 'Multi-dimensional Data',
        desc: 'Supports search index, media index, demand graph, and more',
      },
      easyUse: {
        title: 'Easy to Use',
        desc: 'Intuitive UI, simplified operations, quick data retrieval',
      },
      export: {
        title: 'Flexible Export',
        desc: 'Multiple export formats for further analysis',
      },
      monitor: {
        title: 'Real-time Monitoring',
        desc: 'Monitor task status in real-time, detect and handle exceptions',
      },
      trend: {
        title: 'Trend Analysis',
        desc: 'Built-in trend analysis to help you understand market dynamics',
      },
    },
    techStack: {
      title: 'Tech Stack',
      frontend: 'Frontend',
      backend: 'Backend',
      dataProcess: 'Data Processing',
    },
    faq: {
      title: 'FAQ',
      q1: 'What is BaiduIndexHunter?',
      a1: 'BaiduIndexHunter is a Baidu Index data collection tool for learning, helping you understand keyword trends, regional distribution, and more. For personal learning only.',
      q2: 'How to get started?',
      a2: 'First configure your database and Redis in settings, then add your Baidu Cookie, finally enter keywords in data collection page to start.',
      q3: 'How long does data collection take?',
      a3: 'Depends on keyword count, time range, and regions. Uses smart crawling with 0.1-0.3s intervals. Use task scheduler for large data collection.',
      q4: 'What export formats are supported?',
      a4: 'CSV, Excel, and JSON. Exported data contains complete time series for in-depth analysis.',
      q5: 'How to ensure stable data collection?',
      a5: 'Built-in Cookie pool, smart rate limiting, and breakpoint resume for automatic recovery after interruption.',
      q6: 'Can this project be used commercially?',
      a6: 'No. This project is for personal learning only. Commercial use is strictly prohibited. Users bear all legal responsibilities.',
    },
    projectInfo: {
      title: 'Project Info',
      personalProject: {
        title: 'Personal Project',
        desc: 'This is a personal learning project, for learning only, no external services provided.',
      },
      disclaimer: {
        title: 'Disclaimer',
        desc: 'For learning only. Commercial use prohibited. Users bear all responsibilities.',
      },
      techLearning: {
        title: 'Tech Learning',
        desc: 'Learn crawling, task scheduling, data visualization through this project.',
      },
      localUse: {
        title: 'Local Use',
        desc: 'Designed for local use, no server deployment or external services.',
      },
    },
  },

  // Privacy
  privacy: {
    title: 'Privacy Policy & Disclaimer',
    lastUpdated: 'Last Updated',
    disclaimer: {
      title: 'Important Notice',
      content: 'This project is for personal learning only. Commercial use is strictly prohibited. All responsibilities are borne by the user.',
    },
    sections: {
      projectNature: {
        title: 'Project Nature',
        intro: 'BaiduIndexHunter is a personal learning project for studying web crawling and data analysis:',
        items: [
          'Learning only: For technical learning and research purposes',
          'Local use: Designed to run locally, no external services',
          'Non-commercial: Commercial use is strictly prohibited',
          'At your own risk: Users bear all consequences',
        ],
      },
      dataNote: {
        title: 'Data Notice',
        intro: 'All data is stored locally on your computer:',
        items: [
          'Local storage: All settings, cookies, and results are stored locally',
          'No remote transfer: Data is never sent to remote servers',
          'User control: You have full control over all local data',
        ],
      },
      cookieNote: {
        title: 'Cookie Usage',
        intro: 'This project requires your Baidu Cookie to access data. Please note:',
        items: [
          'Cookies are stored in your local database only',
          'Do not share your cookies with others',
          'Update cookies regularly',
          'Stop using if account issues occur',
        ],
      },
      risks: {
        title: 'Usage Risks',
        intro: 'Please understand these risks before using:',
        items: [
          'Account risk: Frequent requests may cause account restrictions',
          'Legal risk: Unauthorized data collection may violate laws',
          'Data accuracy: Collected data is for reference only',
        ],
        note: 'By using this project, you accept these risks.',
      },
      disclaimerTerms: {
        title: 'Disclaimer Terms',
        items: [
          'Provided "as is" without any warranties',
          'Author not responsible for any direct or indirect damages',
          'No guarantees on data accuracy or completeness',
          'Users bear all legal issues',
          'May stop maintenance at any time without notice',
        ],
      },
      compliance: {
        title: 'Compliance',
        intro: 'Please follow these principles:',
        items: [
          'Comply with applicable laws and regulations',
          'Follow Baidu Index terms of service',
          'Control request frequency to avoid server burden',
          'Use collected data for personal learning only',
          'Do not use collected data for commercial purposes',
        ],
      },
      contact: {
        title: 'Contact',
        content: 'For questions about this policy, please contact the author through project channels.',
      },
    },
  },
}
