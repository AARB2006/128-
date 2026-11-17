import { createRouter, createWebHistory } from 'vue-router'
import { initAuth, useAuth } from '@/composables/useAuth.js'
import LandingView from '@/views/LandingView.vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import MusicLibraryView from '@/views/MusicLibraryView.vue'
import ImportMusicView from '@/views/ImportMusicView.vue'
import PlaylistsView from '@/views/PlaylistsView.vue'
import ExportMusicView from '@/views/ExportMusicView.vue'
import AccountView from '@/views/AccountView.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  {
    // Every signed-in page lives under /app and shares one layout (sidebar).
    path: '/app',
    component: AppLayout,
    meta: { requiresAuth: true },
    redirect: { name: 'library' },
    children: [
      { path: 'library', name: 'library', component: MusicLibraryView },
      { path: 'import', name: 'import', component: ImportMusicView },
      { path: 'playlists', name: 'playlists', component: PlaylistsView },
      { path: 'export', name: 'export', component: ExportMusicView },
      { path: 'account', name: 'account', component: AccountView },
    ],
  },
  // Anything unknown goes to the landing page.
  { path: '/:pathMatch(.*)*', redirect: { name: 'landing' } },
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
    return { name: 'library' }
  }
})

export default router