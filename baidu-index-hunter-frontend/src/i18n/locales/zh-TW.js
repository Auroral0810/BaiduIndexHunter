// 繁體中文
export default {
  // 通用
  common: {
    appName: 'BaiduIndexHunter',
    version: 'v2.0',
    save: '儲存',
    cancel: '取消',
    confirm: '確認',
    delete: '刪除',
    edit: '編輯',
    add: '新增',
    refresh: '重新整理',
    search: '搜尋',
    filter: '篩選',
    reset: '重設',
    loading: '載入中...',
    success: '成功',
    error: '錯誤',
    warning: '警告',
    info: '提示',
    noData: '暫無資料',
    total: '共',
    items: '條',
    page: '頁',
    actions: '操作',
    status: '狀態',
    createTime: '建立時間',
    updateTime: '更新時間',
    learningProject: '學習專案',
  },

  // 導航選單
  nav: {
    home: '首頁',
    dataCollection: '資料採集',
    cookieManager: 'Cookie管理',
    dashboard: '資料大屏',
    settings: '設定資訊',
    about: '關於專案',
    privacy: '隱私政策',
  },

  // 頁尾
  footer: {
    disclaimer: '本專案僅供個人學習交流使用，嚴禁用於商業用途。使用本專案產生的一切責任由使用者自行承擔。',
    copyright: '© {year} BaiduIndexHunter - 學習專案',
    aboutProject: '關於專案',
    privacyPolicy: '隱私政策',
  },

  // 首頁
  home: {
    title: '百度指數資料採集系統',
    subtitle: '高效、穩定的百度指數資料採集工具',
    startNow: '開始採集',
    learnMore: '瞭解更多',
    featuresTitle: '核心特性',
    workflowTitle: '使用流程',
    features: {
      efficient: {
        title: '高效爬取',
        desc: '優化的爬取策略，智慧管理Cookie，確保爬取效率和成功率',
      },
      multiData: {
        title: '多維度資料',
        desc: '支援搜尋指數、媒體指數等多維度資料採集，滿足不同研究需求',
      },
      timeDimension: {
        title: '豐富的時間維度',
        desc: '支援日度、週度資料，可靈活選擇時間範圍和對比時間',
      },
      multiTerminal: {
        title: '多終端支援',
        desc: '區分PC和行動端資料，全面瞭解使用者行為特徵',
      },
      smartExport: {
        title: '智慧匯出',
        desc: '支援Excel、CSV等多種格式匯出，資料處理更便捷',
      },
      stable: {
        title: '穩定可靠',
        desc: '智慧Cookie池管理，保障長時間穩定採集',
      },
    },
    workflow: {
      step1: { title: '選擇關鍵詞', desc: '輸入關鍵詞或上傳檔案' },
      step2: { title: '選擇時間範圍', desc: '自訂採集的時間範圍' },
      step3: { title: '選擇城市', desc: '全國或特定城市資料' },
      step4: { title: '選擇資料類型', desc: '搜尋指數、媒體指數等' },
      step5: { title: '開始採集', desc: '一鍵獲取所需資料' },
    },
    cta: {
      title: '開始學習資料採集技術',
      description: '本專案幫助您學習爬蟲技術、任務調度、資料視覺化等多方面技能。',
      button: '立即開始',
    },
  },

  // 資料採集頁
  dataCollection: {
    title: '百度指數資料採集',
    status: {
      running: '服務運行中',
      disconnected: '服務未連線',
    },
    tabs: {
      searchIndex: '搜尋指數',
      feedIndex: '資訊指數',
      wordGraph: '需求圖譜',
      demographicAttributes: '人群屬性',
      interestProfile: '興趣分析',
      regionDistribution: '地域分佈',
      taskList: '任務列表',
    },
    dialog: {
      title: 'API服務狀態',
      normal: 'API服務正常',
      abnormal: 'API服務異常',
      normalDesc: '服務連線正常，可以正常採集資料',
      abnormalDesc: '無法連線到API服務，請確保後端服務已啟動',
      apiAddress: 'API地址',
    },
    progress: {
      currentTask: '當前任務',
      progress: '進度',
      running: '正在執行...',
    },
    // Keep existing keys below
    title: '資料採集',
    apiStatus: 'API狀態',
    connected: '服務執行中',
    disconnected: '服務未連接',
    taskTypes: {
      searchIndex: '搜尋指數',
      feedIndex: '資訊指數',
      wordGraph: '需求圖譜',
      demographic: '人群屬性',
      interest: '興趣分佈',
      region: '地域分佈',
    },
    form: {
      keywords: '關鍵詞',
      keywordsPlaceholder: '請輸入關鍵詞，多個關鍵詞用逗號分隔',
      dateRange: '時間範圍',
      region: '地域',
      allRegion: '全國',
      priority: '優先級',
      submit: '建立任務',
    },
  },

  // Cookie管理頁
  cookieManager: {
    title: 'Cookie 管理',
    stats: {
      total: '總數',
      available: '可用',
      tempBanned: '臨時封禁',
      permBanned: '永久封禁',
    },
    actions: {
      testAll: '測試全部可用性',
      updateStatus: '更新Cookie狀態',
      cleanExpired: '清理過期Cookie',
      syncRedis: '同步到Redis',
      updateAbSr: '更新ab_sr',
      batchBan: '批量封禁所有Cookie',
      batchUnban: '批量解封所有Cookie',
    },
    table: {
      name: 'Cookie名',
      fieldCount: '欄位數量',
      value: 'Cookie值',
      status: '狀態',
      expireTime: '過期時間',
      neverExpire: '永不過期',
    },
    status: {
      available: '可用',
      tempBanned: '臨時封禁',
      permBanned: '永久封禁',
      expired: '已過期',
    },
  },

  // 資料大屏
  dashboard: {
    title: '百度指數爬蟲資料大屏',
    selectTaskType: '選擇任務類型',
    selectPeriod: '統計週期',
    allStats: '全部統計',
    periods: {
      last24h: '最近24小時',
      last3d: '最近3天',
      last7d: '最近7天',
      last30d: '最近30天',
      last90d: '最近90天',
      last180d: '最近半年',
      last365d: '最近一年',
      allTime: '全部時間',
      custom: '自訂時間範圍',
    },
    stats: {
      totalTasks: '總任務數',
      completedTasks: '完成任務',
      failedTasks: '失敗任務',
      totalItems: '資料總量',
      crawledItems: '爬取條數',
      successRate: '成功率',
      avgDuration: '平均耗時',
    },
    charts: {
      taskTrend: '任務執行趨勢',
      dataTrend: '資料爬取趨勢',
      successRate: '任務成功率對比',
      avgDuration: '平均執行時間對比',
      dataVolume: '資料爬取量對比',
    },
  },

  // 設定頁
  settings: {
    title: '系統設定',
    groups: {
      task: '任務設定',
      spider: '爬蟲設定',
      cookie: 'Cookie設定',
      output: '輸出設定',
      ui: '介面設定',
    },
    ui: {
      theme: '介面主題',
      themeLight: '淺色模式',
      themeDark: '深色模式',
      language: '介面語言',
      languageTip: '選擇介面顯示語言，部分內容需重新整理頁面後生效',
      themeTip: '選擇介面顯示主題，立即生效',
      localStorageNote: '介面設定儲存在本機瀏覽器中，不會同步到伺服器。',
    },
    configs: {
      'task.max_concurrent_tasks': '最大並發任務數',
      'task.queue_check_interval': '任務佇列檢查間隔（秒）',
      'task.default_priority': '預設任務優先級（1-10）',
      'task.max_retry_count': '任務最大重試次數',
      'task.retry_delay': '任務重試延遲（秒）',
      'spider.min_interval': '請求間隔最小秒數',
      'spider.max_interval': '請求間隔最大秒數',
      'spider.retry_times': '請求失敗重試次數',
      'spider.timeout': '請求超時時間（秒）',
      'spider.max_workers': '最大工作執行緒數',
      'spider.user_agent_rotation': '是否輪換User-Agent',
      'spider.proxy_enabled': '是否啟用代理',
      'spider.proxy_url': '代理URL',
      'spider.failure_multiplier': '失敗後間隔倍數',
      'output.default_format': '預設輸出格式',
      'output.csv_encoding': 'CSV檔案編碼',
      'output.excel_sheet_name': 'Excel工作表名稱',
      'output.file_name_template': '檔案名稱範本',
      'cookie.block_cooldown': 'Cookie封禁冷卻時間（秒）',
      'cookie.max_usage_per_day': '每日最大使用次數',
      'cookie.min_available_count': '最小可用Cookie數量',
      'cookie.rotation_strategy': 'Cookie輪換策略',
    },
    actions: {
      save: '儲存設定',
      reset: '重設為預設設定',
    },
    messages: {
      saveSuccess: '設定儲存成功',
      resetSuccess: '設定已重設為預設值',
    },
  },

  // 關於頁
  about: {
    title: '關於 BaiduIndexHunter',
    subtitle: '一個用於學習的百度指數資料採集與分析工具',
    disclaimer: {
      title: '重要聲明',
      content1: '本專案僅供個人學習和技術研究使用，嚴禁用於任何商業用途。',
      content2: '如果您將本專案用於商業目的或造成任何損失，由此產生的一切法律責任和後果由使用者自行承擔，與專案作者無關。使用本專案即表示您已閱讀並同意此聲明。',
    },
    intro: {
      title: '專案介紹',
      p1: 'BaiduIndexHunter是一個用於學習的個人專案，旨在幫助開發者學習和研究網路爬蟲技術、資料採集與分析方法。',
      p2: '透過本專案，您可以學習到：Cookie管理機制、任務排程系統設計、分散式架構思想、資料視覺化展示等多方面的技術知識。',
      p3: '本專案採用 Vue 3 + Flask + Scrapy 技術棧，程式碼結構清晰，註解完善，適合作為學習參考。',
    },
    features: {
      title: '技術特點',
      scrapy: {
        title: 'Scrapy 框架',
        desc: '採用 Scrapy 框架進行資料採集，支援斷點續傳、安全退出、靈活的中介軟體設定等特性。',
      },
      scheduler: {
        title: '任務排程系統',
        desc: '支援多任務並發執行，智慧負載平衡，任務佇列管理，即時狀態監控。',
      },
      dataTypes: {
        title: '全面的資料類型',
        desc: '支援搜尋指數、資訊指數、需求圖譜、人群畫像、地域分佈、興趣分佈等多種資料類型的採集。',
      },
      resume: {
        title: '斷點續傳機制',
        desc: '採集過程中如遇異常中斷，系統自動儲存進度，重啟後可從斷點繼續，避免重複工作。',
      },
    },
    coreFeatures: {
      title: '核心特性',
      efficient: {
        title: '高效爬取',
        desc: '智慧Cookie管理和負載平衡，確保穩定可靠的資料獲取',
      },
      multiData: {
        title: '多維資料',
        desc: '支援搜尋指數、媒體指數、需求圖譜等多種資料類型',
      },
      easyUse: {
        title: '易於使用',
        desc: '直觀的使用者介面，簡化複雜操作，快速獲取所需資料',
      },
      export: {
        title: '靈活匯出',
        desc: '支援多種格式匯出，便於進一步分析和處理',
      },
      monitor: {
        title: '即時監控',
        desc: '即時監控任務執行狀態，及時發現和處理異常情況',
      },
      trend: {
        title: '趨勢分析',
        desc: '內建趨勢分析工具，幫助您洞察市場動態和使用者需求',
      },
    },
    techStack: {
      title: '技術架構',
      frontend: '前端技術',
      backend: '後端技術',
      dataProcess: '資料處理',
    },
    faq: {
      title: '常見問題',
      q1: 'BaiduIndexHunter是什麼？',
      a1: 'BaiduIndexHunter是一個用於學習和研究的百度指數資料採集工具，幫助您了解關鍵詞搜尋趨勢、地域分佈等資料分析方法。本專案僅供個人學習交流使用。',
      q2: '如何開始使用？',
      a2: '首先在設定頁面設定您的資料庫和Redis連接資訊，然後新增您的百度帳號Cookie，最後在資料採集頁面輸入關鍵詞、選擇時間範圍和地域即可開始獲取資料。',
      q3: '資料採集需要多長時間？',
      a3: '採集時間取決於關鍵詞數量、時間範圍和選擇的地域數量。系統採用智慧爬取策略，通常每個請求間隔0.1-0.3秒。大量資料採集建議使用任務排程功能。',
      q4: '支援哪些資料匯出格式？',
      a4: '目前支援CSV、Excel、JSON格式匯出。匯出的資料包含完整的時間序列資訊，可直接匯入Excel或其他資料分析工具進行深度分析。',
      q5: '如何保證資料採集的穩定性？',
      a5: '系統內建Cookie池管理機制，支援多帳號輪換使用；採用智慧限流策略，避免觸發反爬機制；提供任務斷點續傳功能，異常中斷後可自動恢復。',
      q6: '這個專案可以用於商業用途嗎？',
      a6: '不可以。本專案僅供個人學習和技術研究使用，嚴禁用於任何商業用途。如果您將本專案用於商業目的，由此產生的一切法律責任和後果由使用者自行承擔。',
    },
    projectInfo: {
      title: '專案資訊',
      personalProject: {
        title: '個人專案',
        desc: '本專案為個人學習專案，僅供學習交流使用，不對外提供任何服務。',
      },
      disclaimer: {
        title: '免責聲明',
        desc: '本專案僅供學習研究使用，嚴禁商業用途。使用者需自行承擔使用本專案產生的一切責任。',
      },
      techLearning: {
        title: '技術學習',
        desc: '透過本專案您可以學習到爬蟲技術、任務排程、資料視覺化等多方面的開發技能。',
      },
      localUse: {
        title: '本機使用',
        desc: '本專案設計為本機執行使用，不涉及伺服器部署和對外提供服務。',
      },
    },
  },

  // 隱私政策頁
  privacy: {
    title: '隱私政策與免責聲明',
    lastUpdated: '最後更新',
    disclaimer: {
      title: '重要聲明',
      content: '本專案僅供個人學習和技術研究使用，嚴禁用於任何商業用途。如果您將本專案用於商業目的或造成任何損失，由此產生的一切法律責任和後果由使用者自行承擔，與專案作者無關。',
    },
    sections: {
      projectNature: {
        title: '專案性質',
        intro: 'BaiduIndexHunter 是一個個人學習專案，旨在幫助開發者學習和研究網路爬蟲技術、資料採集與分析方法。本專案：',
        items: [
          '僅供學習交流：本專案僅用於技術學習和研究目的',
          '本機執行：設計為在本機電腦上執行，不涉及對外提供服務',
          '非商業用途：嚴禁將本專案用於任何商業目的',
          '風險自負：使用本專案產生的任何後果由使用者自行承擔',
        ],
      },
      dataNote: {
        title: '資料說明',
        intro: '由於本專案設計為本機執行，所有資料均儲存在您的本機電腦上：',
        items: [
          '本機儲存：所有設定資訊、Cookie資料、採集結果均儲存在本機資料庫',
          '無遠端傳輸：本專案不會將您的資料傳輸到任何遠端伺服器',
          '使用者自主管理：您對本機儲存的所有資料擁有完全控制權',
        ],
      },
      cookieNote: {
        title: 'Cookie 使用說明',
        intro: '本專案需要您提供百度帳號的 Cookie 資訊來存取百度指數資料。請注意：',
        items: [
          'Cookie 資訊僅儲存在您的本機資料庫中',
          '請勿將 Cookie 資訊分享給他人',
          '定期更新 Cookie 以確保其有效性',
          '如果帳號出現異常，請立即停止使用並更換 Cookie',
        ],
      },
      risks: {
        title: '使用風險',
        intro: '使用本專案可能存在以下風險，請您充分了解：',
        items: [
          '帳號風險：頻繁請求可能導致百度帳號被限制或封禁',
          '法律風險：未經授權採集資料可能違反相關法律法規',
          '資料準確性：採集的資料僅供參考，不保證其準確性和完整性',
        ],
        note: '您在使用本專案前應充分了解並評估上述風險，使用本專案即表示您已接受這些風險。',
      },
      disclaimerTerms: {
        title: '免責條款',
        items: [
          '本專案按「原樣」提供，不提供任何形式的明示或暗示保證',
          '專案作者不對使用本專案造成的任何直接或間接損失負責',
          '專案作者不對資料的準確性、完整性或可用性做任何保證',
          '使用本專案導致的任何法律問題由使用者自行承擔',
          '本專案可能隨時停止維護，恕不另行通知',
        ],
      },
      compliance: {
        title: '合規使用',
        intro: '請您在使用本專案時遵守以下原則：',
        items: [
          '遵守中華人民共和國相關法律法規',
          '遵守百度指數的使用條款和服務協議',
          '合理控制請求頻率，避免對目標伺服器造成負擔',
          '僅將採集的資料用於個人學習和研究',
          '不得將採集的資料用於任何商業用途',
        ],
      },
      contact: {
        title: '聯繫方式',
        content: '如果您對本隱私政策有任何疑問，請透過專案相關管道聯繫作者。',
      },
    },
  },
}
