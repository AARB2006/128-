import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

if (!url || !key) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_PUBLISHABLE_KEY. ' +
      'Copy .env.example to .env.local and fill them in.',
  )
}

// Uses the publishable key only. Row Level Security decides what each signed-in
// user can read or change; the service_role key must never reach the browser.
export const supabase = createClient(url, key, {
  auth: { flowType: 'pkce' },
})