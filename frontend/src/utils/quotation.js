import { parseColor } from '@/utils'
import { call } from 'frappe-ui'
import { ref, toValue, watch } from 'vue'

// Indicator colours come from the server (crm.api.quotation.get_indicator) and
// follow ERPNext's list: red / orange / yellow / green / gray / blue ...

// Colour name -> indicator dot text class, same helper Deal statuses use.
export function indicatorClass(color) {
  return parseColor(color || 'gray')
}

// Colour name -> nearest frappe-ui Badge theme.
export function indicatorTheme(color) {
  return (
    {
      red: 'red',
      orange: 'orange',
      yellow: 'orange',
      green: 'green',
      blue: 'blue',
      'light-blue': 'blue',
    }[color] || 'gray'
  )
}

// Symbols come from the ERPNext Currency record, fetched once per currency.
const symbolCache = {}

async function fetchCurrencySymbol(currency) {
  if (!(currency in symbolCache)) {
    symbolCache[currency] = call('crm.api.quotation.get_currency_symbol', { currency }).catch(
      () => '',
    )
  }
  return symbolCache[currency]
}

// A function that formats an amount with the symbol of `currency` (a ref or getter).
// A currency with no symbol on its record shows its code instead (e.g. "CNY 388.00").
export function useCurrencyFormat(currency) {
  const symbol = ref(null)

  watch(
    () => toValue(currency),
    async (code) => {
      symbol.value = null
      if (!code) return
      const found = await fetchCurrencySymbol(code)
      if (code === toValue(currency)) symbol.value = found
    },
    { immediate: true },
  )

  return (value) => {
    const number = new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Math.abs(value || 0))
    const code = toValue(currency)
    // Until the symbol arrives nothing is prefixed, so the screen doesn't flash the code.
    const prefix = symbol.value === null ? '' : symbol.value || `${code} `
    return `${value < 0 ? '-' : ''}${prefix}${number}`
  }
}

// Tax lines a quotation / sales order always shows under Taxable Amount, ₹0.00
// when absent, matched on the tax row's description. Any other tax row with an
// amount follows them, then Rounding.
const FIXED_TAX_LINES = ['CGST', 'SGST', 'IGST', 'Freight']

export function totalsLines(doc) {
  const taxes = doc?.taxes || []
  const matches = (tax, name) => (tax.description || '').toUpperCase().includes(name.toUpperCase())
  const sum = (rows) => rows.reduce((total, t) => total + (Number(t.tax_amount) || 0), 0)
  const lines = FIXED_TAX_LINES.map((name) => ({
    label: name,
    value: sum(taxes.filter((t) => matches(t, name))),
  }))
  for (const tax of taxes) {
    if (!FIXED_TAX_LINES.some((name) => matches(tax, name)) && Number(tax.tax_amount))
      lines.push({ label: tax.description, value: Number(tax.tax_amount) })
  }
  const rounding = doc?.rounded_total ? doc.rounded_total - (doc.grand_total || 0) : 0
  lines.push({ label: 'Rounding', value: Math.abs(rounding) >= 0.005 ? rounding : 0 })
  return lines
}

// The server sends the address one part per line: street line(s), then
// "city, state, pincode", country, and "GSTIN: ...". Split for the address
// card: the street lines as one paragraph, "City, State - Pincode, Country"
// as the place line, and the GSTIN on its own. A line's own trailing comma is
// dropped so none doubles up.
export function addressParts(text) {
  const lines = (text || '')
    .split('\n')
    .map((l) => l.trim().replace(/^,+|,+$/g, '').trim())
    .filter(Boolean)
  const gstinLine = lines.find((l) => /^GSTIN:/i.test(l))
  const rest = lines.filter((l) => l !== gstinLine)
  // Country and the city line are the last two; anything before is street.
  const tail = rest.length > 2 ? rest.slice(-2) : rest.slice(rest.length > 1 ? 1 : 0)
  const street = rest.slice(0, rest.length - tail.length)
  const place = tail.map((l) => l.replace(/,\s*(\d{6})$/, ' - $1')).join(', ')
  return {
    street: street.join(', '),
    place,
    gstin: gstinLine ? gstinLine.replace(/^GSTIN:\s*/i, '') : '',
  }
}
