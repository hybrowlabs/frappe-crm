// Data fields that render as a +91 prefixed 10 digit phone input.
// Fields with options "Phone" are picked up automatically; add a
// doctype/fieldname here only for fields that don't carry that option.
export const PHONE_FIELDS = {
  'CRM Call Log': ['from', 'to'],
}

export function isPhoneField(doctype, field) {
  if (field.fieldtype !== 'Data') return false
  return (
    field.options === 'Phone' || PHONE_FIELDS[doctype]?.includes(field.fieldname)
  )
}

/** Strip the +91 country code and any formatting, leaving the digits. */
export function phoneDigits(value) {
  let digits = String(value ?? '').replace(/\D/g, '')
  if (digits.length > 10 && digits.startsWith('91')) digits = digits.slice(2)
  return digits
}

/** Whether a phone value holds exactly ten digits. */
export function isTenDigitPhone(value) {
  return phoneDigits(value).length === 10
}

/**
 * Walk a fields layout and return an error message for the first phone field on
 * `doc` that doesn't hold exactly ten digits, or null when everything is fine.
 * Layout driven, so any field the form renders as a phone input is covered.
 * Empty values are left to the usual mandatory checks.
 */
export function validatePhoneFieldsInLayout(doctype, doc, tabs) {
  for (const tab of tabs || []) {
    for (const section of tab.sections || []) {
      for (const column of section.columns || []) {
        for (const field of column.fields || []) {
          if (!isPhoneField(doctype, field)) continue

          const value = doc?.[field.fieldname]
          if (!value || isTenDigitPhone(value)) continue

          return __('{0} must be a 10 digit number', [__(field.label)])
        }
      }
    }
  }

  return null
}
