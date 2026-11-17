<script setup>
import { onMounted, ref } from 'vue'
import { supabase } from '@/lib/supabase.js'
import { useAuth } from '@/composables/useAuth.js'

const { user } = useAuth()

const profile = ref(null)
const loading = ref(true)
const error = ref('')

// Dev-only check that row-level security is isolating users.
const isDev = import.meta.env.DEV
const visibleProfiles = ref(null)

onMounted(async () => {
  // Read from the profiles table (not from the Google token) so this page
  // exercises the same RLS-protected path the rest of the app uses.
  const { data, error: err } = await supabase
    .from('profiles')
    .select('id, display_name, email')
    .eq('id', user.value.id)
    .maybeSingle()

  if (err) {
    error.value = err.message
  } else if (!data) {
    error.value =
      'Your profile was not found. Try logging out and signing in again.'
  } else {
    profile.value = data
  }
  loading.value = false

  if (isDev) {
    // Ask for EVERY profile row. RLS should return only this user's own.
    const { count } = await supabase
      .from('profiles')
      .select('id', { count: 'exact', head: true })
    visibleProfiles.value = count
  }
})
</script>

<template>
  <section class="app-page">
    <h1 class="app-page-title">Account</h1>

    <div class="app-card">
      <p v-if="loading" class="app-muted">Loading…</p>

      <dl v-else-if="profile" class="details">
        <dt>Name</dt>
        <dd>{{ profile.display_name }}</dd>
        <dt>Email</dt>
        <dd>{{ profile.email }}</dd>
      </dl>

      <p v-if="error" class="app-alert" role="alert">{{ error }}</p>

      <p v-if="isDev && visibleProfiles !== null" class="dev-check">
        Data separation check: you can see {{ visibleProfiles }} profile
        row(s). Expected: 1.
        <strong>{{ visibleProfiles === 1 ? 'OK' : 'CHECK RLS' }}</strong>
      </p>
    </div>
  </section>
</template>

<style scoped>
.details {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 24px;
  margin: 0;
}

dt {
  font-weight: bold;
}

dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.dev-check {
  margin: 16px 0 0;
  font-size: 14px;
  color: var(--c-muted);
}
</style>