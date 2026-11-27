/*
Logging out: a short, visible transition, a real sign-out, then a fresh page.
*/

import { ref } from 'vue'
import { supabase } from '@/lib/supabase.js'
import { useAuth } from './useAuth.js'

// Long enough to read "Logging you out…", short enough not to annoy.
const MIN_DURATION_MS = 900

// Shared by the account menu and the overlay.
const signingOut = ref(false)
const error = ref('')

export function useSignOut() {
  const { signOut } = useAuth()

  async function signOutNow() {
    if (signingOut.value) return
    signingOut.value = true
    error.value = ''

    const pause = new Promise((resolve) => setTimeout(resolve, MIN_DURATION_MS))

    // Supabase removes the session from this browser first, then asks its
    // server to revoke the refresh token so it can never be used again.
    // If that request fails (offline), this device is still signed out: the
    // token is gone from it.
    try {
      await signOut()
    } catch {
      // Checked below: what matters is whether a session is left here.
    }

    let stillSignedIn = true
    try {
      const { data } = await supabase.auth.getSession()
      stillSignedIn = Boolean(data.session)
    } catch {
      // Treat an unreadable session as still signed in, and say so.
    }
    await pause

    if (stillSignedIn) {
      signingOut.value = false
      error.value = "Couldn't log out. Please try again."
      return
    }

    // A full page load (not a router redirect) clears everything the app kept
    // in memory: songs, playlists, export progress. The overlay stays up until
    // the landing page replaces it, and Back can't return to the app because
    // the router guard now finds no session.
    window.location.replace('/')
  }

  function clearError() {
    error.value = ''
  }

  return { signingOut, error, signOutNow, clearError }
}
