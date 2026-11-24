/*
App entry point: creates the Vue app and mounts it.
*/

import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import './style.css'

createApp(App).use(router).mount('#app')