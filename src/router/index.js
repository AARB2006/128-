/*
App routes, plus a guard that sends signed-out users to the landing page.
*/

import { createRouter, createWebHistory } from 'vue-router'
import { initAuth, useAuth } from '@/composables/useAuth.js'
import LandingView from '@/views/LandingView.vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import MusicLibraryView from '@/views/MusicLibraryView.vue'
import ImportMusicView from '@/views/ImportMusicView.vue'
import PlaylistsView from '@/views/PlaylistsView.vue'
import PlaylistNewView from '@/views/PlaylistNewView.vue'
import PlaylistDetailView from '@/views/PlaylistDetailView.vue'
import ExportHistoryView from '@/views/ExportHistoryView.vue'

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
      {
        // No component of its own: the three pages below fill the same outlet,
        // and the sidebar's Playlists link stays highlighted on all of them.
        path: 'playlists',
        children: [
          { path: '', name: 'playlists', component: PlaylistsView },
          { path: 'new', name: 'playlist-new', component: PlaylistNewView },
          { path: ':playlistId', name: 'playlist', component: PlaylistDetailView },
        ],
      },
      { path: 'export-history', name: 'export-history', component: ExportHistoryView },
      // The old Export Music address still works.
      { path: 'export', redirect: { name: 'export-history' } },
      // The Account page was removed; its old address goes to the library.
      { path: 'account', redirect: { name: 'library' } },
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