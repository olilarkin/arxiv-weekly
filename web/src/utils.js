/** Strip a leading circled-number prefix (e.g. ①). */
export function stripPrefix(text) {
  return text?.replace(/^[①-⑨]\s*/, '') ?? ''
}

/** Read the filter state from the URL query string. */
export function readUrlState(search = window.location.search) {
  const p = new URLSearchParams(search)
  return {
    toDate:            p.get('week') || null,
    fromDate:          p.get('from') || null,
    activeCat:         p.get('cat')  || 'all',
    search:            p.get('q')    || '',
    sortByCitations:   p.get('sort') === '1',
    showFavoritesOnly: p.get('fav')  === '1',
  }
}

/** Serialize the filter state into a URL query string. */
export function buildUrlSearch({ toDate, fromDate, activeCat, search, sortByCitations, showFavoritesOnly }) {
  const p = new URLSearchParams()
  if (toDate)              p.set('week', toDate)
  if (fromDate)            p.set('from', fromDate)
  if (activeCat !== 'all') p.set('cat',  activeCat)
  if (search)              p.set('q',    search)
  if (sortByCitations)     p.set('sort', '1')
  if (showFavoritesOnly)   p.set('fav',  '1')
  return p.toString() ? `?${p}` : ''
}
