// The product chain a salesperson picked in Req. Discussion, rendered read-only
// in the later stage forms. Karatage is deliberately left out — it is an
// alloy-only attribute and gets its own field next to the chain, so the two
// stay readable instead of overflowing one narrow input.
export function productChain(deal) {
  const d = deal || {}
  return [d.product_category, d.product_sub_category, d.product_variant]
    .filter(Boolean)
    .join(' → ')
}
