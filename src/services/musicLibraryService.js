/*
Supabase calls to load and delete library songs.
*/

import { supabase } from '@/lib/supabase.js'

// Neither function takes a user id. The signed-in session identifies the user,
// and the row-level-security policies on `songs` decide which rows are visible
// or deletable.

// Supabase returns at most 1,000 rows per request by default, so the library
// is read in batches of this size until a batch comes back short.
const BATCH_SIZE = 1000

export async function getSongs() {
  const data = []

  for (let from = 0; ; from += BATCH_SIZE) {
    const { data: batch, error } = await supabase
      .from('songs')
      .select(
        'song_id, title, source_url, video_id, duration_seconds, date_added, ' +
          'playlist_songs(playlists(playlist_id, name))',
      )
      // song_id breaks ties, so no song is skipped or repeated between batches.
      .order('date_added', { ascending: false })
      .order('song_id', { ascending: true })
      .range(from, from + BATCH_SIZE - 1)

    if (error) throw error
    data.push(...batch)
    if (batch.length < BATCH_SIZE) break
  }

  // Each song gets a `playlists` list of { playlist_id, name }, A to Z.
  return data.map(({ playlist_songs, ...song }) => ({
    ...song,
    playlists: (playlist_songs ?? [])
      .map((link) => link.playlists)
      .filter(Boolean)
      .sort((a, b) => a.name.localeCompare(b.name)),
  }))
}

// Keeps each request's URL short when many songs are selected.
const CHUNK_SIZE = 100

/**
 * Deletes the given songs and returns the ids that were actually deleted.
 * RLS silently skips rows the user doesn't own instead of raising an error, so
 * the caller must compare the returned ids with what it asked for.
 */
export async function deleteSongs(songIds) {
  const deleted = []

  for (let i = 0; i < songIds.length; i += CHUNK_SIZE) {
    const chunk = songIds.slice(i, i + CHUNK_SIZE)

    const { data, error } = await supabase
      .from('songs')
      .delete()
      .in('song_id', chunk)
      .select('song_id')

    if (error) throw error
    deleted.push(...data.map((row) => row.song_id))
  }

  return deleted
}