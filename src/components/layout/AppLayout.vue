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
  <div class="app-shell">
    <header class="mobile-bar">
      <button
        class="menu-btn"
        type="button"
        aria-label="Open navigation"
        :aria-expanded="mobileOpen"
        @click="mobileOpen = true"
      >
        <SidebarIcon name="menu" />
      </button>
      <span class="mobile-title">YT-MP3</span>
    </header>

    <AppSidebar :mobile-open="mobileOpen" @close="mobileOpen = false" />
    <div v-if="mobileOpen" class="scrim" @click="mobileOpen = false" />

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.mobile-bar {
  display: none;
}

.scrim {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: rgba(17, 24, 39, 0.45);
}

@media (max-width: 768px) {
  .app-shell {
    flex-direction: column;
  }

  .mobile-bar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--c-border);
    background: var(--c-surface);
  }

  .menu-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border: 0;
    border-radius: 10px;
    background: transparent;
    color: var(--c-text);
    cursor: pointer;
  }

  .menu-btn:hover {
    background: var(--c-hover);
  }

  .mobile-title {
    font-weight: bold;
  }
}
</style>