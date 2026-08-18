import { productChain } from '@/components/StageForms/productContext'

describe('productChain', () => {
  it('returns an empty string when there is no product chain', () => {
    expect(productChain(null)).toBe('')
    expect(productChain(undefined)).toBe('')
    expect(productChain({})).toBe('')
  })

  it('joins the chain with arrows and skips missing levels', () => {
    expect(
      productChain({
        product_category: 'Alloys',
        product_sub_category: 'Casting Alloys',
        product_variant: 'Palladium Alloys',
      }),
    ).toBe('Alloys → Casting Alloys → Palladium Alloys')
    expect(productChain({ product_category: 'Machines' })).toBe('Machines')
  })

  it('keeps karatage out of the chain — it is shown as its own field', () => {
    expect(
      productChain({
        product_category: 'Alloys',
        product_sub_category: 'Casting Alloys',
        product_variant: 'Palladium Alloys',
        karatage: '14 Kt',
      }),
    ).toBe('Alloys → Casting Alloys → Palladium Alloys')
  })
})
