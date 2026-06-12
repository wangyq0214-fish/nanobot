import { createApp } from 'vue'
import 'katex/dist/katex.min.css'
import './styles/variables.css'
import './styles/base.css'
import App from './App.vue'
import router from './router/index.js'

const app = createApp(App)
app.use(router)
app.mount('#app')