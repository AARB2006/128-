/*
Talks to the backend and Supabase for exports:
start, cancel, history, download, delete.
*/

import { supabase } from '@/lib/supabase.js'
import { ApiError } from './apiError.js'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

// Mirrors MAX_EXPORT_SONGS on the backend (the server enforces it either way).
export const MAX_EXPORT_SONGS = Number(import.meta.env.VITE_MAX_EXPORT_SONGS) || 100

// One export and its songs in one query. History stores only references
// (which playlist, which song at which position), so the playlist's name and
// each song's title are read from `playlists` and `songs` here. Row-level
// security means a user can only ever read their own exports.
const EXPORT_COLUMNS =
  'export_id, playlist_id, status, percent, total_songs, exported_songs, ' +
  'error_message, file_size_bytes, created_at, completed_at, file_expires_at, ' +
  'playlist:playlists(name, playlist_songs(count)), ' +
  'export_items(position, status, error_message, song:songs(title))'

const ACTIVE = ['pending', 'processing', 'packaging']

// Flatten the joined rows into what the pages use:
//   playlist_name  the playlist's current name (null if it was deleted)
//   playlist       { name, song_count } now, or null if it was deleted
//   export_items   in position order, each with `title` (null if the song was
//                  removed from the library)
function toExport(row) {
  if (!row) return null
  const { playlist, export_items: items, ...rest } = row
  return {
    ...rest,
    playlist_name: playlist?.name ?? null,
    playlist: playlist
      ? { name: playlist.name, song_count: playlist.playlist_songs?.[0]?.count ?? 0 }
      : null,
    export_items: [...(items ?? [])]
      .sort((a, b) => a.position - b.position)
      .map(({ song, ...item }) => ({ ...item, title: song?.title ?? null })),
  }
}

// Call the backend with the user's login token, using the same error
// handling as the import service.
async function send(method, path, body, fallbackMessage) {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    throw new ApiError(401, 'You must be signed in to export playlists.')
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(
      0,
      'Could not reach the export server. Make sure the backend is running.',
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

    throw new ApiError(response.status, message || fallbackMessage)
  }

  return data
}

const post = (path, body, fallbackMessage) => send('POST', path, body, fallbackMessage)

/** Start exporting a playlist. Resolves with { export_id, total_songs }. */
export function startExport(playlistId) {
  return post(
    '/exports',
    { playlist_id: playlistId, format: 'zip' },
    'The export could not be started.',
  )
}

export function cancelExport(exportId) {
  return post(`/exports/${exportId}/cancel`, undefined, 'The export could not be cancelled.')
}

/** Remove one finished export from the history (and delete its ZIP). */
export function deleteExport(exportId) {
  return send('DELETE', `/exports/${exportId}`, undefined, 'The export could not be deleted.')
}

/** Remove every finished export from the history. Resolves with { deleted }. */
export function clearExportHistory() {
  return send('DELETE', '/exports', undefined, 'Your history could not be deleted.')
}

export async function getExport(exportId) {
  const { data, error } = await supabase
    .from('exports')
    .select(EXPORT_COLUMNS)
    .eq('export_id', exportId)
    .maybeSingle()

  if (error) throw error
  return toExport(data)
}

// The user's export that is still running, if any (e.g. after a page reload).
export async function getActiveExport() {
  const { data, error } = await supabase
    .from('exports')
    .select(EXPORT_COLUMNS)
    .in('status', ACTIVE)
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle()

  if (error) throw error
  return toExport(data)
}

// Recent exports that produced a file, newest first.
export async function getExportHistory(limit = 50) {
  const { data, error } = await supabase
    .from('exports')
    .select(EXPORT_COLUMNS)
    .in('status', ['completed', 'partial'])
    .order('created_at', { ascending: false })
    .limit(limit)

  if (error) throw error
  return data.map(toExport)
}

/**
 * Download a finished export. The server hands out a link that works for 60
 * seconds, and the browser downloads it like any other file (it shows its own
 * progress, and a large ZIP is never held in this page's memory).
 */
export async function downloadExport(exportId) {
  let path
  try {
    ;({ path } = await post(
      `/exports/${exportId}/download-link`,
      undefined,
      'The download could not be started.',
    ))
  } catch (e) {
    if (e.status === 410) {
      throw new ApiError(410, 'This export has expired. Export the playlist again.')
    }
    throw e
  }

  const link = document.createElement('a')
  link.href = `${API_BASE_URL}${path}`
  link.rel = 'noopener'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

export function isExpired(row, now = Date.now()) {
  return !row?.file_expires_at || new Date(row.file_expires_at).getTime() <= now
}
