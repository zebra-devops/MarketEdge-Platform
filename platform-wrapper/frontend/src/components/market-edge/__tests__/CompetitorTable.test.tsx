import React from 'react'
import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { CompetitorTable } from '../CompetitorTable'
import { Competitor } from '@/types/market-edge'

// Mock Heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  ChevronUpIcon: ({ className }: { className?: string }) => 
    <svg data-testid="chevron-up" className={className}>up</svg>,
  ChevronDownIcon: ({ className }: { className?: string }) => 
    <svg data-testid="chevron-down" className={className}>down</svg>,
  EyeIcon: ({ className }: { className?: string }) => 
    <svg data-testid="eye-icon" className={className}>view</svg>,
  PencilIcon: ({ className }: { className?: string }) => 
    <svg data-testid="pencil-icon" className={className}>edit</svg>,
  GlobeAltIcon: ({ className }: { className?: string }) => 
    <svg data-testid="globe-icon" className={className}>globe</svg>,
  BuildingOfficeIcon: ({ className }: { className?: string }) => 
    <svg data-testid="building-icon" className={className}>building</svg>,
}))

describe('CompetitorTable Component', () => {
  const user = userEvent.setup()

  const mockCompetitors: Competitor[] = [
    {
      id: 'comp-1',
      name: 'Alpha Corp',
      business_type: 'Technology',
      market_share_estimate: 25.5,
      tracking_priority: 4,
      website: 'https://alpha-corp.com',
      last_updated: '2023-12-01T10:00:00Z',
    },
    {
      id: 'comp-2',
      name: 'Beta LLC',
      business_type: 'Retail',
      market_share_estimate: 18.3,
      tracking_priority: 2,
      website: 'https://beta-llc.com',
      last_updated: '2023-11-28T15:30:00Z',
    },
    {
      id: 'comp-3',
      name: 'Gamma Industries',
      business_type: 'Manufacturing',
      market_share_estimate: null,
      tracking_priority: 5,
      website: null,
      last_updated: null,
    },
  ]

  const defaultProps = {
    competitors: mockCompetitors,
    isLoading: false,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock current date for consistent last_updated formatting
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2023-12-05T12:00:00Z'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders table with competitors data', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('Alpha Corp')).toBeInTheDocument()
    expect(screen.getByText('Beta LLC')).toBeInTheDocument()
    expect(screen.getByText('Gamma Industries')).toBeInTheDocument()
  })

  it('displays loading state', () => {
    render(<CompetitorTable {...defaultProps} isLoading={true} />)
    
    expect(screen.getByText('Loading competitors...')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('displays empty state when no competitors', () => {
    render(<CompetitorTable {...defaultProps} competitors={[]} />)
    
    expect(screen.getByText('No competitors')).toBeInTheDocument()
    expect(screen.getByText('Get started by adding competitors to track in this market.')).toBeInTheDocument()
    expect(screen.getByTestId('building-icon')).toBeInTheDocument()
  })

  it('renders all table headers', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    expect(screen.getByText('Competitor')).toBeInTheDocument()
    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Market Share')).toBeInTheDocument()
    expect(screen.getByText('Priority')).toBeInTheDocument()
    expect(screen.getByText('Last Updated')).toBeInTheDocument()
  })

  it('formats market share correctly', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    expect(screen.getByText('25.5%')).toBeInTheDocument()
    expect(screen.getByText('18.3%')).toBeInTheDocument()
    expect(screen.getByText('N/A')).toBeInTheDocument() // For null market share
  })

  it('displays priority badges with correct styling', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const highPriority = screen.getByText('High')
    expect(highPriority).toHaveClass('bg-orange-100', 'text-orange-800')
    
    const belowAveragePriority = screen.getByText('Below Average')
    expect(belowAveragePriority).toHaveClass('bg-blue-100', 'text-blue-800')
    
    const criticalPriority = screen.getByText('Critical')
    expect(criticalPriority).toHaveClass('bg-red-100', 'text-red-800')
  })

  it('formats last updated dates correctly', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    expect(screen.getByText('4 days ago')).toBeInTheDocument() // Dec 1
    expect(screen.getByText('1 weeks ago')).toBeInTheDocument() // Nov 28 
    expect(screen.getByText('Never')).toBeInTheDocument() // null date
  })

  it('renders website links correctly', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const alphaLink = screen.getByText('alpha-corp.com')
    expect(alphaLink).toHaveAttribute('href', 'https://alpha-corp.com')
    expect(alphaLink).toHaveAttribute('target', '_blank')
    expect(alphaLink).toHaveAttribute('rel', 'noopener noreferrer')
    
    const betaLink = screen.getByText('beta-llc.com')
    expect(betaLink).toHaveAttribute('href', 'https://beta-llc.com')
  })

  it('handles sorting by name', async () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const nameHeader = screen.getByText('Competitor')
    await user.click(nameHeader)
    
    const rows = screen.getAllByRole('row')
    // First row is header, so check data rows
    expect(rows[1]).toHaveTextContent('Alpha Corp')
    expect(rows[2]).toHaveTextContent('Beta LLC')
    expect(rows[3]).toHaveTextContent('Gamma Industries')
    
    // Click again to sort descending
    await user.click(nameHeader)
    const rowsDesc = screen.getAllByRole('row')
    expect(rowsDesc[1]).toHaveTextContent('Gamma Industries')
    expect(rowsDesc[2]).toHaveTextContent('Beta LLC')
    expect(rowsDesc[3]).toHaveTextContent('Alpha Corp')
  })

  it('handles sorting by market share', async () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const marketShareHeader = screen.getByText('Market Share')
    await user.click(marketShareHeader)
    
    // Should sort by market share ascending (null values last)
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('Beta LLC') // 18.3%
    expect(rows[2]).toHaveTextContent('Alpha Corp') // 25.5%
    expect(rows[3]).toHaveTextContent('Gamma Industries') // null
  })

  it('shows sort indicators correctly', async () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const nameHeader = screen.getByText('Competitor')
    await user.click(nameHeader)
    
    expect(screen.getByTestId('chevron-up')).toBeInTheDocument()
    
    await user.click(nameHeader)
    expect(screen.getByTestId('chevron-down')).toBeInTheDocument()
  })

  it('calls onViewCompetitor when view button is clicked', async () => {
    const onViewCompetitor = jest.fn()
    render(
      <CompetitorTable {...defaultProps} onViewCompetitor={onViewCompetitor} />
    )
    
    const viewButtons = screen.getAllByTestId('eye-icon')
    await user.click(viewButtons[0])
    
    expect(onViewCompetitor).toHaveBeenCalledWith(mockCompetitors[0])
  })

  it('calls onEditCompetitor when edit button is clicked', async () => {
    const onEditCompetitor = jest.fn()
    render(
      <CompetitorTable {...defaultProps} onEditCompetitor={onEditCompetitor} />
    )
    
    const editButtons = screen.getAllByTestId('pencil-icon')
    await user.click(editButtons[0])
    
    expect(onEditCompetitor).toHaveBeenCalledWith(mockCompetitors[0])
  })

  it('does not render action buttons when handlers not provided', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    expect(screen.queryByTestId('eye-icon')).not.toBeInTheDocument()
    expect(screen.queryByTestId('pencil-icon')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<CompetitorTable {...defaultProps} className="custom-table-class" />)
    
    const tableContainer = screen.getByRole('table').closest('div')
    expect(tableContainer).toHaveClass('custom-table-class')
  })

  it('handles null/undefined business types', () => {
    const competitorsWithNullType: Competitor[] = [
      {
        ...mockCompetitors[0],
        business_type: null,
      },
    ]
    
    render(<CompetitorTable competitors={competitorsWithNullType} />)
    
    expect(screen.getByText('Not specified')).toBeInTheDocument()
  })

  it('has proper table structure and accessibility', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const table = screen.getByRole('table')
    expect(table).toHaveClass('min-w-full', 'divide-y', 'divide-gray-200')
    
    const thead = table.querySelector('thead')
    expect(thead).toHaveClass('bg-gray-50')
    
    const tbody = table.querySelector('tbody')
    expect(tbody).toHaveClass('bg-white', 'divide-y', 'divide-gray-200')
  })

  it('has hover effects on rows', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const dataRows = screen.getAllByRole('row').slice(1) // Skip header row
    dataRows.forEach(row => {
      expect(row).toHaveClass('hover:bg-gray-50')
    })
  })

  it('handles responsive design classes', () => {
    render(<CompetitorTable {...defaultProps} />)
    
    const container = screen.getByRole('table').closest('div')
    expect(container).toHaveClass('overflow-x-auto')
    
    const outerContainer = container?.parentElement
    expect(outerContainer).toHaveClass('bg-white', 'rounded-lg', 'border', 'border-gray-200', 'overflow-hidden')
  })
})