import { describe, expect, it } from 'vitest'

import { optionDraftError, validateQuestionDraft } from './questionValidation'

const base = (overrides = {}) =>({
  prompt: '¿Cuántos músculos extraoculares hay?',
  options: ['Cuatro', 'Seis', 'Ocho', 'Doce'],
  correctIndex: 1,
  ...overrides,
})

describe('validateQuestionDraft', () => {
  it('acepta un borrador válido', () => {
    expect(validateQuestionDraft(base()).valid).toBe(true)
  })

  it('rechaza enunciado corto o largo', () => {
    expect(validateQuestionDraft(base({ prompt: 'casi' })).promptOk).toBe(false)
    expect(validateQuestionDraft(base({ prompt: 'x'.repeat(501) })).promptOk).toBe(false)
    expect(validateQuestionDraft(base()).promptOk).toBe(true)
  })

  it('rechaza opciones vacías o repetidas', () => {
    expect(validateQuestionDraft(base({ options: ['a', 'b', 'c', ''] })).optionsOk).toBe(false)
    expect(
      validateQuestionDraft(base({ options: ['A', 'a', 'c', 'd'] })).optionsOk,
    ).toBe(false)
  })

  it('rechaza borradores sin opción correcta marcada', () => {
    expect(validateQuestionDraft(base({ correctIndex: null })).hasCorrect).toBe(false)
  })
})

describe('optionDraftError', () => {
  it('marca vacía y repetida', () => {
    expect(optionDraftError(['a', 'b', 'c', 'a'], 3)).toBe('Esta opción está repetida.')
    expect(optionDraftError(['a', 'b', 'c', ''], 3)).toBe('Esta opción es obligatoria.')
    expect(optionDraftError(['a', 'b', 'c', 'd'], 2)).toBeNull()
  })
})
