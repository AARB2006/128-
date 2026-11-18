<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import SidebarIcon from './SidebarIcon.vue'
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

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
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

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>
