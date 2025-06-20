// Smoke test to verify test setup
import { describe, it, expect } from 'vitest'

describe('Test Setup Verification', () => {
  it('should run a simple test', () => {
    expect(true).toBe(true)
  })

  it('should handle basic math', () => {
    expect(2 + 2).toBe(4)
  })

  it('should work with async tests', async () => {
    const promise = Promise.resolve('success')
    await expect(promise).resolves.toBe('success')
  })
})
