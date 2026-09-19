import { parseColor } from '@/utils'

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

export function formatQuotationAmount(value, currency) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency || 'INR',
  }).format(value || 0)
}
