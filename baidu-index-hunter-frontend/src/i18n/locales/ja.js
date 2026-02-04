// 日本語
export default {
  // 共通
  common: {
    appName: 'BaiduIndexHunter',
    version: 'v2.0',
    save: '保存',
    cancel: 'キャンセル',
    confirm: '確認',
    delete: '削除',
    edit: '編集',
    add: '追加',
    refresh: '更新',
    search: '検索',
    filter: 'フィルター',
    reset: 'リセット',
    loading: '読み込み中...',
    success: '成功',
    error: 'エラー',
    warning: '警告',
    info: '情報',
    noData: 'データなし',
    total: '合計',
    items: '件',
    page: 'ページ',
    actions: '操作',
    status: '状態',
    createTime: '作成日時',
    updateTime: '更新日時',
    learningProject: '学習プロジェクト',
  },

  // ナビゲーション
  nav: {
    home: 'ホーム',
    dataCollection: 'データ収集',
    cookieManager: 'Cookie管理',
    dashboard: 'ダッシュボード',
    settings: '設定',
    about: 'プロジェクトについて',
    privacy: 'プライバシー',
  },

  // フッター
  footer: {
    disclaimer: '本プロジェクトは個人学習用です。商用利用は固く禁じられています。利用者は全ての責任を負います。',
    copyright: '© {year} BaiduIndexHunter - 学習プロジェクト',
    aboutProject: 'プロジェクトについて',
    privacyPolicy: 'プライバシーポリシー',
  },

  // ホーム
  home: {
    title: '百度指数データ収集システム',
    subtitle: '効率的で安定した百度指数データ収集ツール',
    startNow: '収集開始',
    learnMore: '詳細を見る',
    featuresTitle: 'コア機能',
    workflowTitle: 'ワークフロー',
    features: {
      efficient: {
        title: '効率的な収集',
        desc: '最適化された収集戦略とスマートCookie管理で高効率を実現',
      },
      multiData: {
        title: '多次元データ',
        desc: '検索指数、メディア指数など複数のデータタイプをサポート',
      },
      timeDimension: {
        title: '柔軟な時間範囲',
        desc: '日次・週次データ対応、カスタマイズ可能な時間範囲',
      },
      multiTerminal: {
        title: 'マルチ端末対応',
        desc: 'PCとモバイルデータを区別し、ユーザー行動を総合分析',
      },
      smartExport: {
        title: 'スマートエクスポート',
        desc: 'Excel、CSVなど複数形式でデータ処理を便利に',
      },
      stable: {
        title: '安定・信頼性',
        desc: 'スマートCookieプール管理で長時間安定収集',
      },
    },
    workflow: {
      step1: { title: 'キーワード選択', desc: 'キーワード入力またはファイルアップロード' },
      step2: { title: '時間範囲選択', desc: '収集期間をカスタマイズ' },
      step3: { title: '地域選択', desc: '全国または特定都市' },
      step4: { title: 'データタイプ選択', desc: '検索指数、メディア指数など' },
      step5: { title: '収集開始', desc: 'ワンクリックでデータ取得' },
    },
    cta: {
      title: 'データ収集技術を学ぶ',
      description: 'このプロジェクトでクローリング、タスクスケジューリング、データ可視化などを学べます。',
      button: '今すぐ始める',
    },
  },

  // データ収集
  dataCollection: {
    title: '百度指数データ収集',
    status: {
      running: 'サービス稼働中',
      disconnected: 'サービス未接続',
    },
    tabs: {
      searchIndex: '検索指数',
      feedIndex: 'ニュース指数',
      wordGraph: '需要グラフ',
      demographicAttributes: '人口属性',
      interestProfile: '興味分析',
      regionDistribution: '地域分布',
      taskList: 'タスク一覧',
    },
    dialog: {
      title: 'APIサービス状態',
      normal: 'APIサービス正常',
      abnormal: 'APIサービスエラー',
      normalDesc: '接続成功、データ収集可能',
      abnormalDesc: 'APIに接続できません、バックエンドが起動しているか確認してください',
      apiAddress: 'APIアドレス',
    },
    progress: {
      currentTask: '現在のタスク',
      progress: '進捗',
      running: '実行中...',
    },
    // Keep existing keys below
    title: 'データ収集',
    apiStatus: 'API状態',
    connected: 'サービス稼働中',
    disconnected: 'サービス未接続',
    taskTypes: {
      searchIndex: '検索指数',
      feedIndex: 'フィード指数',
      wordGraph: 'ワードグラフ',
      demographic: '人口統計',
      interest: '興味分布',
      region: '地域分布',
    },
    form: {
      keywords: 'キーワード',
      keywordsPlaceholder: 'キーワードを入力（カンマ区切り）',
      dateRange: '期間',
      region: '地域',
      allRegion: '全国',
      priority: '優先度',
      submit: 'タスク作成',
    },
  },

  // Cookie管理
  cookieManager: {
    title: 'Cookie 管理',
    stats: {
      total: '総数',
      available: '利用可能',
      tempBanned: '一時禁止',
      permBanned: '永久禁止',
    },
    actions: {
      testAll: '全てテスト',
      updateStatus: '状態更新',
      cleanExpired: '期限切れ削除',
      syncRedis: 'Redisに同期',
      updateAbSr: 'ab_sr更新',
      batchBan: '全Cookie禁止',
      batchUnban: '全Cookie解除',
    },
    table: {
      name: 'Cookie名',
      fieldCount: 'フィールド数',
      value: 'Cookie値',
      status: '状態',
      expireTime: '有効期限',
      neverExpire: '無期限',
    },
    status: {
      available: '利用可能',
      tempBanned: '一時禁止',
      permBanned: '永久禁止',
      expired: '期限切れ',
    },
  },

  // ダッシュボード
  dashboard: {
    title: '百度指数クローラーダッシュボード',
    selectTaskType: 'タスクタイプ選択',
    selectPeriod: '統計期間',
    allStats: '全統計',
    periods: {
      last24h: '過去24時間',
      last3d: '過去3日',
      last7d: '過去7日',
      last30d: '過去30日',
      last90d: '過去90日',
      last180d: '過去半年',
      last365d: '過去1年',
      allTime: '全期間',
      custom: 'カスタム期間',
    },
    stats: {
      totalTasks: '総タスク数',
      completedTasks: '完了タスク',
      failedTasks: '失敗タスク',
      totalItems: 'データ総量',
      crawledItems: '取得件数',
      successRate: '成功率',
      avgDuration: '平均所要時間',
    },
    charts: {
      taskTrend: 'タスク実行傾向',
      dataTrend: 'データ取得傾向',
      successRate: '成功率比較',
      avgDuration: '平均所要時間比較',
      dataVolume: 'データ量比較',
    },
  },

  // 設定
  settings: {
    title: 'システム設定',
    groups: {
      task: 'タスク設定',
      spider: 'スパイダー設定',
      cookie: 'Cookie設定',
      output: '出力設定',
      ui: 'UI設定',
    },
    ui: {
      theme: 'テーマ',
      themeLight: 'ライトモード',
      themeDark: 'ダークモード',
      language: '言語',
      languageTip: '表示言語を選択。一部の内容はページ更新後に反映されます。',
      themeTip: '表示テーマを選択。即座に反映されます。',
      localStorageNote: 'UI設定はブラウザのローカルストレージに保存され、サーバーには同期されません。',
    },
    configs: {
      'task.max_concurrent_tasks': '最大同時タスク数',
      'task.queue_check_interval': 'キューチェック間隔（秒）',
      'task.default_priority': 'デフォルト優先度（1-10）',
      'task.max_retry_count': '最大リトライ回数',
      'task.retry_delay': 'リトライ遅延（秒）',
      'spider.min_interval': '最小リクエスト間隔（秒）',
      'spider.max_interval': '最大リクエスト間隔（秒）',
      'spider.retry_times': 'リクエストリトライ回数',
      'spider.timeout': 'リクエストタイムアウト（秒）',
      'spider.max_workers': '最大ワーカー数',
      'spider.user_agent_rotation': 'User-Agentローテーション',
      'spider.proxy_enabled': 'プロキシ有効',
      'spider.proxy_url': 'プロキシURL',
      'spider.failure_multiplier': '失敗時間隔倍率',
      'output.default_format': 'デフォルト出力形式',
      'output.csv_encoding': 'CSVエンコーディング',
      'output.excel_sheet_name': 'Excelシート名',
      'output.file_name_template': 'ファイル名テンプレート',
      'cookie.block_cooldown': 'Cookieブロッククールダウン（秒）',
      'cookie.max_usage_per_day': '1日あたり最大使用回数',
      'cookie.min_available_count': '最小利用可能数',
      'cookie.rotation_strategy': 'ローテーション戦略',
    },
    actions: {
      save: '設定を保存',
      reset: 'デフォルトにリセット',
    },
    messages: {
      saveSuccess: '設定が保存されました',
      resetSuccess: '設定がデフォルトにリセットされました',
    },
  },

  // プロジェクトについて
  about: {
    title: 'BaiduIndexHunterについて',
    subtitle: '学習用の百度指数データ収集・分析ツール',
    disclaimer: {
      title: '重要なお知らせ',
      content1: '本プロジェクトは個人学習・技術研究専用です。商用利用は固く禁じられています。',
      content2: '本プロジェクトを商用目的で使用した場合、または損害が発生した場合、全ての法的責任は利用者が負うものとします。本プロジェクトの使用は、この声明に同意したものとみなされます。',
    },
    intro: {
      title: 'プロジェクト紹介',
      p1: 'BaiduIndexHunterは、開発者がWebクローリング技術、データ収集・分析手法を学ぶための個人学習プロジェクトです。',
      p2: '本プロジェクトを通じて学べること：Cookie管理メカニズム、タスクスケジューリングシステム設計、分散アーキテクチャ概念、データ可視化など。',
      p3: 'Vue 3 + Flask + Scrapy技術スタックで構築され、コード構造が明確でコメントも充実しており、学習参考に適しています。',
    },
    features: {
      title: '技術的特徴',
      scrapy: {
        title: 'Scrapyフレームワーク',
        desc: 'Scrapyによるデータ収集、中断からの再開、安全な終了、柔軟なミドルウェア設定をサポート。',
      },
      scheduler: {
        title: 'タスクスケジューラー',
        desc: '並行タスク実行、スマートな負荷分散、キュー管理、リアルタイム監視をサポート。',
      },
      dataTypes: {
        title: '包括的なデータタイプ',
        desc: '検索指数、フィード指数、ワードグラフ、人口統計、地域・興味分布をサポート。',
      },
      resume: {
        title: '中断からの再開',
        desc: '中断時に自動保存、再起動後に中断点から継続し、重複作業を回避。',
      },
    },
    coreFeatures: {
      title: 'コア機能',
      efficient: {
        title: '効率的なクローリング',
        desc: 'スマートCookie管理と負荷分散で安定したデータ収集を実現',
      },
      multiData: {
        title: '多次元データ',
        desc: '検索指数、メディア指数、需要グラフなど多種をサポート',
      },
      easyUse: {
        title: '使いやすさ',
        desc: '直感的なUI、簡略化された操作、迅速なデータ取得',
      },
      export: {
        title: '柔軟なエクスポート',
        desc: '複数の形式でエクスポート可能',
      },
      monitor: {
        title: 'リアルタイム監視',
        desc: 'タスク状態をリアルタイムで監視、例外を検出・対処',
      },
      trend: {
        title: 'トレンド分析',
        desc: '内蔵のトレンド分析で市場動向を把握',
      },
    },
    techStack: {
      title: '技術スタック',
      frontend: 'フロントエンド',
      backend: 'バックエンド',
      dataProcess: 'データ処理',
    },
    faq: {
      title: 'よくある質問',
      q1: 'BaiduIndexHunterとは？',
      a1: '百度指数データ収集の学習ツールです。キーワードトレンド、地域分布などを理解するのに役立ちます。個人学習専用です。',
      q2: '使い方は？',
      a2: 'まず設定でデータベースとRedisを設定し、百度Cookieを追加、データ収集ページでキーワードを入力して開始します。',
      q3: 'データ収集にかかる時間は？',
      a3: 'キーワード数、期間、地域数によります。スマートクローリングで0.1-0.3秒間隔。大量収集にはタスクスケジューラーをお勧めします。',
      q4: 'どのエクスポート形式がサポートされていますか？',
      a4: 'CSV、Excel、JSON。完全な時系列データを含み、詳細分析に利用できます。',
      q5: '安定したデータ収集を確保するには？',
      a5: '内蔵のCookieプール、スマートレート制限、中断からの自動再開機能があります。',
      q6: 'このプロジェクトを商用利用できますか？',
      a6: 'いいえ。個人学習専用です。商用利用は固く禁じられています。全ての法的責任は利用者が負います。',
    },
    projectInfo: {
      title: 'プロジェクト情報',
      personalProject: {
        title: '個人プロジェクト',
        desc: '本プロジェクトは個人学習用であり、外部サービスは提供しません。',
      },
      disclaimer: {
        title: '免責事項',
        desc: '学習専用です。商用利用禁止。利用者は全ての責任を負います。',
      },
      techLearning: {
        title: '技術学習',
        desc: 'クローリング、タスクスケジューリング、データ可視化を学べます。',
      },
      localUse: {
        title: 'ローカル使用',
        desc: 'ローカル使用を想定しており、サーバーデプロイや外部サービスは含みません。',
      },
    },
  },

  // プライバシーポリシー
  privacy: {
    title: 'プライバシーポリシーと免責事項',
    lastUpdated: '最終更新',
    disclaimer: {
      title: '重要なお知らせ',
      content: '本プロジェクトは個人学習専用です。商用利用は固く禁じられています。全ての責任は利用者が負います。',
    },
    sections: {
      projectNature: {
        title: 'プロジェクトの性質',
        intro: 'BaiduIndexHunterはWebクローリングとデータ分析を学ぶための個人学習プロジェクトです：',
        items: [
          '学習専用：技術学習・研究目的のみ',
          'ローカル使用：ローカルで実行するよう設計、外部サービスなし',
          '非商用：商用利用は固く禁止',
          '自己責任：全ての結果は利用者が負担',
        ],
      },
      dataNote: {
        title: 'データに関する注意',
        intro: '全てのデータはローカルコンピュータに保存されます：',
        items: [
          'ローカル保存：全ての設定、Cookie、結果はローカルに保存',
          '遠隔転送なし：データはリモートサーバーに送信されません',
          'ユーザー管理：全てのローカルデータを完全に制御できます',
        ],
      },
      cookieNote: {
        title: 'Cookieの使用について',
        intro: 'データアクセスには百度Cookieが必要です。ご注意ください：',
        items: [
          'Cookieはローカルデータベースにのみ保存',
          'Cookieを他者と共有しないでください',
          '定期的にCookieを更新してください',
          'アカウント異常時は使用を中止してください',
        ],
      },
      risks: {
        title: '使用リスク',
        intro: '使用前にこれらのリスクを理解してください：',
        items: [
          'アカウントリスク：頻繁なリクエストでアカウント制限の可能性',
          '法的リスク：無許可のデータ収集は法律違反の可能性',
          'データ精度：収集データは参考用であり、精度は保証されません',
        ],
        note: '本プロジェクトの使用により、これらのリスクを受け入れたものとみなされます。',
      },
      disclaimerTerms: {
        title: '免責条項',
        items: [
          '「現状のまま」提供され、いかなる保証もありません',
          '作者は直接的・間接的な損害に対して責任を負いません',
          'データの精度や完全性は保証されません',
          '全ての法的問題は利用者が負担します',
          '予告なくメンテナンスを中止する場合があります',
        ],
      },
      compliance: {
        title: 'コンプライアンス',
        intro: '以下の原則に従ってください：',
        items: [
          '適用される法律・規制を遵守',
          '百度指数の利用規約を遵守',
          'サーバー負荷を避けるためリクエスト頻度を制御',
          '収集データは個人学習のみに使用',
          '収集データを商用利用しないこと',
        ],
      },
      contact: {
        title: 'お問い合わせ',
        content: 'ご質問は、プロジェクトチャンネルを通じて作者にお問い合わせください。',
      },
    },
  },
}
