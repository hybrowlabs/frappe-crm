// Data fields that render as a +91 prefixed 10 digit phone input.
// Add a doctype/fieldname here and the field gets the phone control plus the
// "must be 10 digits" check before the document is saved.
export const PHONE_FIELDS = {
  'CRM Call Log': ['from', 'to'],
}

export function isPhoneField(doctype, field) {
  if (field.fieldtype !== 'Data') return false
  return (
    field.options === 'Phone' || PHONE_FIELDS[doctype]?.includes(field.fieldname)
  )
}

/**
 * Return an error message when a phone field on `doc` doesn't hold exactly ten
 * digits (the +91 country code is ignored), or null when everything is fine.
 * Empty values are left to the usual mandatory checks.
 */
export function validatePhoneFields(doctype, doc, getLabel) {
  const fieldnames = PHONE_FIELDS[doctype] || []

  for (const fieldname of fieldnames) {
    const value = doc?.[fieldname]
    if (!value) continue

    let digits = String(value).replace(/\D/g, '')
    if (digits.length > 10 && digits.startsWith('91')) digits = digits.slice(2)

    if (digits.length !== 10) {
      const label = getLabel?.(fieldname) || fieldname
      return __('{0} must be a 10 digit number', [__(label)])
    }
  }

  return null
}
