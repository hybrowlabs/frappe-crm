// Quantities shown the way the ERPNext desk shows a Float with no precision of
// its own: a whole number with no decimals, anything else with the system's 3,
// both with Indian digit grouping (1,500 / 2.500 / 1,500.250).
const QTY_PRECISION = 3

export function formatQty(value) {
  if (value === null || value === undefined || value === '') return ''
  const n = Number(value)
  if (!Number.isFinite(n)) return String(value)
  const decimals = Number.isInteger(n) ? 0 : QTY_PRECISION
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n)
}
