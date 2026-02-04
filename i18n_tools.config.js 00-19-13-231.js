module.exports = {
    entry: ['baidu-index-hunter-frontend/src/i18n/locales'], // 提取、还原、遗漏扫描入口文件夹，可以配置多个,默认是 src
    outDir: 'baidu-index-hunter-frontend/src/i18n/locales', // i18n 输出文件夹 默认是 src/locales
    outShow:1, //输出文件展示结构 1 扁平化结构 2树级结构 默认扁平化
    exclude: ['baidu-index-hunter-frontend/src/i18n/locales'], // 不提取的文件夹, 默认是 ['src/locales']
    extensions: ['.vue', '.js', '.ts'], // 提取的文件后缀名，默认是 ['.js', '.vue', '.ts']
    filename: 'zh_CN', // 输出的文件名,默认为 zh_cn
    extname: 'js', //  输出的文件后缀名默认为 js  ,支持json和js（js格式为 module.exports = {} 或 export default {}），
    langList: ['en', 'zh-CN', 'zh-TW', 'ja', 'ko', 'ru', 'fr', 'de', 'es'] // 翻译目标语言列表，包含：英语、简体中文、繁体中文、日语、韩语、俄语、法语、德语、西班牙语。注意：使用不同的翻译接口，需要更换对应的语言编码
} 