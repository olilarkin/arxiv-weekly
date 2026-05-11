import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Header from '../components/Header'

describe('Header', () => {
  it('renders site title', () => {
    render(<Header total={0} loading={false} />)
    expect(screen.getByText('Audio AI Weekly')).toBeInTheDocument()
  })

  it('shows paper count when not loading and total > 0', () => {
    render(<Header total={42} loading={false} />)
    expect(screen.getByText(/Showing 42 papers/)).toBeInTheDocument()
  })

  it('hides paper count when loading', () => {
    render(<Header total={42} loading={true} />)
    expect(screen.queryByText(/42/)).not.toBeInTheDocument()
  })

  it('hides paper count when total is 0', () => {
    render(<Header total={0} loading={false} />)
    expect(screen.queryByText(/Showing/)).not.toBeInTheDocument()
  })

  it('renders subtitle text', () => {
    render(<Header total={0} loading={false} />)
    expect(screen.getByText(/Audio Foundation Models/)).toBeInTheDocument()
  })
})
