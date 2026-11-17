<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import SidebarIcon from './SidebarIcon.vue'

defineProps({
  // Only used on small screens, where the sidebar is a slide-out drawer.
  mobileOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

const router = useRouter()
const { user, signOut } = useAuth()

// Sidebar state stays local: one boolean doesn't need a store.
const collapsed = ref(false)
const signingOut = ref(false)
const signOutError = ref('')

const items = [
  { name: 'library', label: 'Music Library', icon: 'music' },
  { name: 'import', label: 'Import Music', icon: 'import' },
  { name: 'playlists', label: 'Playlists', icon: 'list' },
  { name: 'export', label: 'Export Music', icon: 'export' },
  { name: 'account', label: 'Account', icon: 'user' },
]

const displayName = computed(
  () => user.value?.user_metadata?.full_name || user.value?.email || '',
)
const initial = computed(() => displayName.value.charAt(0).toUpperCase())

async function onSignOut() {
  signingOut.value = true
  signOutError.value = ''
  try {
    await signOut()
    router.replace({ name: 'landing' })
  } catch (e) {
    signOutError.value = e.message || 'Could not log out.'
    signingOut.value = false
  }
}
</script>

<template>
  <aside
    class="sidebar"
    :class="{ collapsed, open: mobileOpen }"
    aria-label="Main navigation"
  >
    <div class="sidebar-head">
      <span class="brand">
        <SidebarIcon name="music" />
        <span class="label">YT-MP3</span>
      </span>

      <button
        class="icon-btn collapse-btn"
        type="button"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-expanded="!collapsed"
        @click="collapsed = !collapsed"
      >
        <SidebarIcon name="chevron" :class="{ flipped: collapsed }" />
      </button>

      <button
        class="icon-btn close-btn"
        type="button"
        aria-label="Close navigation"
        @click="emit('close')"
      >
        <SidebarIcon name="close" />
      </button>
    </div>

    <nav class="nav">
      <RouterLink
        v-for="item in items"
        :key="item.name"
        :to="{ name: item.name }"
        class="nav-item"
        active-class="active"
        :title="collapsed ? item.label : undefined"
        :aria-label="item.label"
      >
        <SidebarIcon :name="item.icon" />
        <span class="label">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar-foot">
      <div v-if="displayName" class="user">
        <span class="avatar" aria-hidden="true">{{ initial }}</span>
        <span class="label user-name">{{ displayName }}</span>
      </div>

      <button
        class="nav-item"
        type="button"
        :disabled="signingOut"
        :title="collapsed ? 'Log Out' : undefined"
        aria-label="Log Out"
        @click="onSignOut"
      >
        <SidebarIcon name="logout" />
        <span class="label">{{ signingOut ? 'Logging out…' : 'Log Out' }}</span>
      </button>

      <p v-if="signOutError" class="sign-out-error" role="alert">
        {{ signOutError }}
      </p>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 240px;
  flex-shrink: 0;
  padding: 16px 12px;
  border-right: 1px solid var(--c-border);
  background: var(--c-surface);
}

.sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 4px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--c-muted);
  cursor: pointer;
}

.icon-btn:hover {
  background: var(--c-hover);
  color: var(--c-text);
}

.flipped {
  transform: rotate(180deg);
}

.close-btn {
  display: none;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--c-muted);
  font: inherit;
  font-size: 15px;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
}

.nav-item:hover:not(:disabled) {
  background: var(--c-hover);
  color: var(--c-text);
}

.nav-item.active {
  background: var(--c-accent);
  color: var(--c-accent-text);
}

.nav-item:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sidebar-foot {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--c-border);
}

.user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px;
}

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--c-hover);
  font-size: 13px;
  font-weight: bold;
}

.user-name {
  overflow: hidden;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sign-out-error {
  margin: 0;
  padding: 0 12px;
  font-size: 13px;
  color: var(--c-danger);
}

/* Desktop: sticky column that can collapse to icons only. */
@media (min-width: 769px) {
  .sidebar {
    position: sticky;
    top: 0;
    height: 100vh;
    transition: width 160ms ease;
  }

  .sidebar.collapsed {
    width: 72px;
  }

  .sidebar.collapsed .label,
  .sidebar.collapsed .brand {
    display: none;
  }

  .sidebar.collapsed .sidebar-head {
    justify-content: center;
  }

  .sidebar.collapsed .nav-item {
    justify-content: center;
  }

  .sidebar.collapsed .user {
    justify-content: center;
    padding: 4px 0;
  }
}

/* Small screens: off-canvas drawer opened from the top bar. */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 30;
    width: 260px;
    transform: translateX(-100%);
    visibility: hidden; /* keeps hidden links out of the tab order */
    transition: transform 160ms ease, visibility 0s linear 160ms;
  }

  .sidebar.open {
    transform: none;
    visibility: visible;
    transition: transform 160ms ease, visibility 0s;
  }

  .collapse-btn {
    display: none;
  }

  .close-btn {
    display: inline-flex;
  }
}
</style>