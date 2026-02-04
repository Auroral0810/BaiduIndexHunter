import { Lang } from 'language-translate/types';
import { defineConfig } from 'language-translate/utils';

const baseDir = './src/i18n/locales/';

export default defineConfig({
    proxy: {
        host: '127.0.0.1',
        port: 7897,
    },
    // 增加翻译延迟（毫秒），防止由于请求过快被 Google 翻译接口屏蔽
    translateRuntimeDelay: 1500,
    // 调整单次写入硬盘的 key 数量
    translateRuntimeChunkSize: 5,
    fromLang: Lang['zh-CN'],
    fromPath: './src/i18n/locales/zh_CN.js',
    translate: [
        {
            label: '将结果翻译到locales文件夹下',
            targetConfig: [
                {
                    targetLang: Lang.en,
                    outPath: `${baseDir}en.js`,
                },
                // 建议移除与 fromLang 相同的 targetLang，避免原地翻译导致失败或冲突
                {
                    targetLang: Lang['zh-TW'],
                    outPath: `${baseDir}zh-TW.js`,
                },
                {
                    targetLang: Lang.ja,
                    outPath: `${baseDir}ja.js`,
                },
                {
                    targetLang: Lang.ko,
                    outPath: `${baseDir}ko.js`,
                },
                {
                    targetLang: Lang.ru,
                    outPath: `${baseDir}ru.js`,
                },
                {
                    targetLang: Lang.fr,
                    outPath: `${baseDir}fr.js`,
                },
                {
                    targetLang: Lang.de,
                    outPath: `${baseDir}de.js`,
                },
                {
                    targetLang: Lang.es,
                    outPath: `${baseDir}es.js`,
                },
            ],
        },
    ],
});