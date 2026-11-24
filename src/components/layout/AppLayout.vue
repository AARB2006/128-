<!--
Page frame for signed-in pages: sidebar, content area
and the export progress card.
-->
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import SidebarIcon from './SidebarIcon.vue'
import ExportProgressToast from '@/components/export/ExportProgressToast.vue'
import { useExportJob } from '@/composables/useExportJob.js'
import '@/assets/app.css'

const route = useRoute()
const mobileOpen = ref(false)

// Close the drawer whenever the user navigates.
watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
  },
)

function onKeydown(event) {
  if (event.key === 'Escape') mobileOpen.value = false
}

// Show the progress card again if an export is still running (after a
// reload, or one started in another tab). Signing out forgets it.
const { job, resume, reset } = useExportJob()

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  resume()
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  reset()
})
</script>

<template>
  <div class="app-shell mobile:flex-col">
    <!-- Only shown on small screens, where the sidebar becomes a drawer. -->
    <header
      class="mobile-bar sticky top-0 z-10 hidden items-center gap-3 border-b border-border bg-surface px-3 py-2 mobile:flex"
    >
      <button
        class="menu-btn inline-flex size-10 cursor-pointer items-center justify-center rounded-[10px] border-0 bg-transparent text-text hover:bg-hover"
        type="button"
        aria-label="Open navigation"
        :aria-expanded="mobileOpen"
        @click="mobileOpen = true"
      >
        <SidebarIcon name="menu" />
      </button>
      <span class="mobile-title font-bold">YT-MP3</span>
    </header>

    <AppSidebar :mobile-open="mobileOpen" @close="mobileOpen = false" />
    <div
      v-if="mobileOpen"
      class="scrim fixed inset-0 z-20 bg-[rgba(17,24,39,0.45)]"
      @click="mobileOpen = false"
    />

    <!-- Extra room at the bottom so the export card never hides the last row. -->
    <main class="app-main" :class="{ 'has-export-card': job }">
      <RouterView />
    </main>

    <ExportProgressToast />
  </div>
</template>

<style scoped>
.has-export-card {
  padding-bottom: 160px;
}
</style>
