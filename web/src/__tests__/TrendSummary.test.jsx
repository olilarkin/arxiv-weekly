import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TrendSummary from '../components/TrendSummary'

describe('TrendSummary', () => {
  it('renders all trend lines', () => {
    const trend = [
      'Audio foundation model research advanced.',
      'Source separation accuracy improved.',
      'Anomalous sound detection drew attention.',
    ]
    render(<TrendSummary trend={trend} />)
    expect(screen.getByText(/Audio foundation model research advanced/)).toBeInTheDocument()
    expect(screen.getByText(/Source separation accuracy improved/)).toBeInTheDocument()
    expect(screen.getByText(/Anomalous sound detection drew attention/)).toBeInTheDocument()
  })

  it('strips circled number prefixes from trend lines', () => {
    const trend = ['① Audio foundation models', '② Source separation']
    render(<TrendSummary trend={trend} />)
    expect(screen.getByText(/Audio foundation models/)).toBeInTheDocument()
    expect(screen.queryByText(/①/)).not.toBeInTheDocument()
  })

  it('renders number prefixes 1. 2. 3.', () => {
    const trend = ['A', 'B', 'C']
    render(<TrendSummary trend={trend} />)
    expect(screen.getByText('1.')).toBeInTheDocument()
    expect(screen.getByText('2.')).toBeInTheDocument()
    expect(screen.getByText('3.')).toBeInTheDocument()
  })

  it('renders empty trend gracefully', () => {
    const { container } = render(<TrendSummary trend={[]} />)
    expect(container.querySelectorAll('div > div').length).toBeGreaterThan(0)
  })

  it('renders section header', () => {
    render(<TrendSummary trend={[]} />)
    expect(screen.getByText(/This week's technical trends/)).toBeInTheDocument()
  })
})
