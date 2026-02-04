import VueI18n from 'vue-i18n'
import Vue from 'vue'
let zh = require('./zh_CN.js')

Vue.use(VueI18n)

export default new VueI18n({
	locale: 'zh',
	messages: {
		zh 
	}
})
