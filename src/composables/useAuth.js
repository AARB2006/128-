import { computed, ref } from 'vue'
import { supabase } from '@/lib/supabase.js'

// Module-level state: every component that calls useAuth() shares it.
const session = ref(null)
const ready = ref(false)
let initPromise = null

/**
 * Loads the current session once and keeps it updated.
 * Safe to call many times; the router guard awaits it before every navigation.
 * On the OAuth return trip, getSession() waits for the code exchange to finish.
 */
export function initAuth() {
  if (!initPromise) {
    initPromise = (async () => {
      const { data } = await supabase.auth.getSession()
      session.value = data.session

      // Keep this callback synchronous. Awaiting other Supabase calls inside it
      // can deadlock the client.
      supabase.auth.onAuthStateChange((_event, newSession) => {
        session.value = newSession
      })

      ready.value = true
    })()
  }
  return initPromise
}

export function useAuth() {
  const user = computed(() => session.value?.user ?? null)
  const isAuthenticated = computed(() => !!session.value)

  async function signInWithGoogle() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/account` },
    })
    if (error) throw error
  }

  async function signOut() {
    const { error } = await supabase.auth.signOut({ scope: 'local' })
    if (error) throw error
  }

  return { session, user, ready, isAuthenticated, signInWithGoogle, signOut }
}