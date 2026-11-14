<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/lib/supabase.js'
import { useAuth } from '@/composables/useAuth.js'

const router = useRouter()
const { user, signOut } = useAuth()

const profile = ref(null)
const loading = ref(true)
const error = ref('')
const signingOut = ref(false)

// Dev-only check that row-level security is isolating users.
const isDev = import.meta.env.DEV
const visibleProfiles = ref(null)

onMounted(async () => {
  // Read from the profiles table (not from the Google token) so this page
  // exercises the same RLS-protected path the rest of the app will use.
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

async function onSignOut() {
  signingOut.value = true
  error.value = ''
  try {
    await signOut()
    router.replace({ name: 'landing' })
  } catch (e) {
    error.value = e.message || 'Could not log out.'
    signingOut.value = false
  }
}
</script>

<template>
  <main class="account">
    <section class="card" aria-labelledby="heading">
      <h1 id="heading">Your account</h1>

      <p v-if="loading">Loading…</p>

      <dl v-else-if="profile" class="details">
        <dt>Name</dt>
        <dd>{{ profile.display_name }}</dd>
        <dt>Email</dt>
        <dd>{{ profile.email }}</dd>
      </dl>

      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <button
        class="action-button"
        type="button"
        :disabled="signingOut"
        @click="onSignOut"
      >
        {{ signingOut ? 'Logging out…' : 'Log out' }}
      </button>

      <p v-if="isDev && visibleProfiles !== null" class="dev-check">
        Data separation check: you can see {{ visibleProfiles }} profile
        row(s). Expected: 1.
        <strong>{{ visibleProfiles === 1 ? 'OK' : 'CHECK RLS' }}</strong>
      </p>
    </section>
  </main>
</template>

<style scoped>
.account {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}

.card {
  width: min(100%, 560px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 48px 32px;
  border: 3px solid #111;
}

h1 {
  margin: 0;
  font-size: 32px;
}

.details {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 16px;
  width: 100%;
  margin: 0;
  font-size: 18px;
}

dt {
  font-weight: bold;
}

dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.error {
  margin: 0;
  color: #b00020;
}

.dev-check {
  margin: 0;
  font-size: 14px;
  color: #555;
  text-align: center;
}

@media (max-width: 640px) {
  .card {
    padding: 32px 20px;
  }
}
</style>