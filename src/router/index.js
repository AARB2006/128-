import { createRouter, createWebHistory } from 'vue-router'
import { initAuth, useAuth } from '@/composables/useAuth.js'
import LandingView from '@/views/LandingView.vue'
import AccountView from '@/views/AccountView.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  {
    path: '/account',
    name: 'account',
    component: AccountView,
    meta: { requiresAuth: true },
  },
]

// The proof-of-concept import/export page stays reachable while developing,
// but is left out of production builds.
if (import.meta.env.DEV) {
  routes.push({
    path: '/poc',
    name: 'poc',
    component: () => import('@/views/PocView.vue'),
  })
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  await initAuth()
  const { isAuthenticated } = useAuth()

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return { name: 'landing' }
  }
  if (to.name === 'landing' && isAuthenticated.value) {
    return { name: 'account' }
  }
})

export default router