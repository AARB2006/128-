// Limits and checks shared by the Add Playlist page and the edit popup.
//
// The 500-character description limit is also enforced by the database. The
// 100-character name limit exists only here, to keep names readable in tables.

export const NAME_MAX = 100
export const DESCRIPTION_MAX = 500

/**
 * Returns the cleaned values to save, or an error message to show.
 * An empty description is stored as null rather than as an empty string.
 */
export function checkPlaylistFields({ name, description }) {
  const cleanName = (name ?? '').trim()
  const cleanDescription = (description ?? '').trim()

  if (!cleanName) return { error: 'Give your playlist a name.' }
  if (cleanName.length > NAME_MAX) {
    return { error: `The name can be at most ${NAME_MAX} characters.` }
  }
  if (cleanDescription.length > DESCRIPTION_MAX) {
    return { error: `The description can be at most ${DESCRIPTION_MAX} characters.` }
  }

  return { name: cleanName, description: cleanDescription || null }
}