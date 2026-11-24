/*
Talks to the backend and Supabase for importing links.
*/

import { supabase } from '@/lib/supabase.js'
import { ApiError } from './apiError.js'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

// A batch and its per-link results in one query. Row-level security means a
// user can only ever read their own batches.
const BATCH_COLUMNS =
  'batch_id, status, total_links, created_at, ' +
  'import_items(line_no, status, error_message, submitted_url)'

function withSortedItems(batch) {
  if (!batch) return null
  return {
    ...batch,
    import_items: [...batch.import_items].sort((a, b) => a.line_no - b.line_no),
  }
}

/**
 * Ask the server to import these links. Resolves as soon as the import has
 * STARTED ({ batch_id, total_links }); progress is read with getBatch().
 */
export async function startImport(urls) {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    throw new ApiError(401, 'You must be signed in to import music.')
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/imports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({ urls }),
    })
  } catch {
    throw new ApiError(
      0,
      'Could not reach the import server. Make sure the backend is running.',
    )
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data.detail
    const message =
      typeof detail === 'object' && detail !== null && !Array.isArray(detail)
        ? detail.message
        : typeof detail === 'string'
          ? detail
          : null

    throw new ApiError(response.status, message || 'The import could not be started.')
  }

  return data
}

export async function getBatch(batchId) {
  const { data, error } = await supabase
    .from('import_batches')
    .select(BATCH_COLUMNS)
    .eq('batch_id', batchId)
    .maybeSingle()

  if (error) throw error
  return withSortedItems(data)
}

// The user's import that is still running, if any (e.g. after a page reload).
export async function getActiveBatch() {
  const { data, error } = await supabase
    .from('import_batches')
    .select(BATCH_COLUMNS)
    .in('status', ['pending', 'processing'])
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle()

  if (error) throw error
  return withSortedItems(data)
}