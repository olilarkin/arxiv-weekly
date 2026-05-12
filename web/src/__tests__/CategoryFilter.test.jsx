import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import CategoryFilter from '../components/CategoryFilter'

const CATS = [
  { id: 'foundation',    label: 'Audio Foundation Models',              color: '#38bdf8', papers: [] },
  { id: 'separation',    label: 'Source Separation',                    color: '#4ade80', papers: [] },
  { id: 'transcription', label: 'Music Transcription & Beat Tracking',  color: '#f472b6', papers: [] },
]

describe('CategoryFilter', () => {
  it('renders the All button', () => {
    render(<CategoryFilter categories={CATS} active="all" onChange={() => {}} />)
    expect(screen.getByText('All')).toBeInTheDocument()
  })

  it('renders all category buttons', () => {
    render(<CategoryFilter categories={CATS} active="all" onChange={() => {}} />)
    expect(screen.getByText('Audio Foundation Models')).toBeInTheDocument()
    expect(screen.getByText('Source Separation')).toBeInTheDocument()
    expect(screen.getByText('Music Transcription & Beat Tracking')).toBeInTheDocument()
  })

  it('calls onChange with correct id when clicked', () => {
    const onChange = vi.fn()
    render(<CategoryFilter categories={CATS} active="all" onChange={onChange} />)
    fireEvent.click(screen.getByText('Source Separation'))
    expect(onChange).toHaveBeenCalledWith('separation')
  })

  it('calls onChange with all when All is clicked', () => {
    const onChange = vi.fn()
    render(<CategoryFilter categories={CATS} active="foundation" onChange={onChange} />)
    fireEvent.click(screen.getByText('All'))
    expect(onChange).toHaveBeenCalledWith('all')
  })

  it('renders nothing for empty categories', () => {
    const { container } = render(<CategoryFilter categories={[]} active="all" onChange={() => {}} />)
    expect(container.querySelectorAll('button')).toHaveLength(1) // only "All"
  })
})
