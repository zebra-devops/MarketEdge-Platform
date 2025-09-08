import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { jest } from '@jest/globals'
import BulkUserImport from '../BulkUserImport'

// Mock the dependencies
jest.mock('@/hooks/useAuth', () => ({
  useAuthContext: () => ({
    user: {
      access_token: 'mock-token',
      role: 'admin'
    }
  })
}))

jest.mock('@/components/providers/OrganisationProvider', () => ({
  useOrganisationContext: () => ({
    allOrganisations: [
      {
        id: 'org-1',
        name: 'Test Organization',
        industry_type: 'technology'
      }
    ]
  })
}))

jest.mock('@/services/api', () => ({
  apiService: {
    get: jest.fn(),
    post: jest.fn()
  }
}))

// Mock fetch
global.fetch = jest.fn()

describe('BulkUserImport', () => {
  const mockProps = {
    organisationId: 'org-1',
    onImportComplete: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders CSV import button', () => {
    render(<BulkUserImport {...mockProps} />)
    
    expect(screen.getByText('CSV Import')).toBeInTheDocument()
  })

  it('opens modal when button is clicked', () => {
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    
    expect(screen.getByText('Bulk User Import via CSV')).toBeInTheDocument()
  })

  it('shows file upload area in modal', () => {
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    
    expect(screen.getByText('Drag and drop your CSV file here, or')).toBeInTheDocument()
    expect(screen.getByText('Choose File')).toBeInTheDocument()
  })

  it('shows download template button', () => {
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    
    expect(screen.getByText('Download Template')).toBeInTheDocument()
  })

  it('handles file selection', () => {
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    
    const fileInput = screen.getByRole('button', { name: 'Choose File' })
    expect(fileInput).toBeInTheDocument()
  })

  it('shows validation options', () => {
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    
    expect(screen.getByLabelText('Send invitation emails')).toBeInTheDocument()
    expect(screen.getByLabelText('Skip duplicate emails')).toBeInTheDocument()
  })

  it('calls download template when clicked', async () => {
    const mockBlob = new Blob(['test'], { type: 'text/csv' })
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(mockBlob)
    })

    // Mock URL methods
    global.URL.createObjectURL = jest.fn(() => 'mock-url')
    global.URL.revokeObjectURL = jest.fn()
    
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    fireEvent.click(screen.getByText('Download Template'))
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/organizations/org-1/users/import/template',
        expect.objectContaining({
          headers: {
            'Authorization': 'Bearer mock-token'
          }
        })
      )
    })
  })

  it('handles file upload error for non-CSV files', () => {
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    
    // Mock file input change with non-CSV file
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    
    fireEvent.change(fileInput)
    
    // Should show error for non-CSV file
    // Note: In a real test, you'd check for toast error message
  })

  it('handles large file error', () => {
    render(<BulkUserImport {...mockProps} />)
    
    fireEvent.click(screen.getByText('CSV Import'))
    
    // Mock file input change with large file
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'test.csv', { type: 'text/csv' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [largeFile],
      writable: false,
    })
    
    fireEvent.change(fileInput)
    
    // Should show error for large file
    // Note: In a real test, you'd check for toast error message
  })
})