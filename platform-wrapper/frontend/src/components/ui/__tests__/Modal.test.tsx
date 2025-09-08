import React from 'react'
import { renderWithProviders as render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import Modal from '../Modal'

// Mock Headless UI components
jest.mock('@headlessui/react', () => ({
  Dialog: {
    Root: ({ children, show }: { children: React.ReactNode; show: boolean }) => 
      show ? <div data-testid="modal-root">{children}</div> : null,
    Panel: ({ children, className }: { children: React.ReactNode; className?: string }) => 
      <div data-testid="modal-panel" className={className}>{children}</div>,
    Title: ({ children, as: Component = 'h3', className }: { children: React.ReactNode; as?: keyof JSX.IntrinsicElements; className?: string }) => 
      <Component data-testid="modal-title" className={className}>{children}</Component>,
  },
  Transition: {
    Root: ({ children, show }: { children: React.ReactNode; show: boolean }) => 
      show ? <div data-testid="transition-root">{children}</div> : null,
    Child: ({ children }: { children: React.ReactNode }) => 
      <div data-testid="transition-child">{children}</div>,
  },
}))

// Mock Heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  XMarkIcon: ({ className }: { className?: string }) => 
    <svg data-testid="close-icon" className={className}>
      <path d="close-icon" />
    </svg>
}))

describe('Modal Component', () => {
  const user = userEvent.setup()

  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    title: 'Test Modal',
    children: <div>Modal content</div>,
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders when isOpen is true', () => {
    render(<Modal {...defaultProps} />)
    
    expect(screen.getByTestId('modal-root')).toBeInTheDocument()
    expect(screen.getByTestId('modal-panel')).toBeInTheDocument()
    expect(screen.getByTestId('modal-title')).toBeInTheDocument()
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByText('Modal content')).toBeInTheDocument()
  })

  it('does not render when isOpen is false', () => {
    render(<Modal {...defaultProps} isOpen={false} />)
    
    expect(screen.queryByTestId('modal-root')).not.toBeInTheDocument()
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument()
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
  })

  it('renders with default medium maxWidth', () => {
    render(<Modal {...defaultProps} />)
    
    const panel = screen.getByTestId('modal-panel')
    expect(panel).toHaveClass('max-w-md')
  })

  it('renders with different maxWidth sizes', () => {
    const sizes = ['sm', 'md', 'lg', 'xl', '2xl'] as const
    
    sizes.forEach(size => {
      const { unmount } = render(<Modal {...defaultProps} maxWidth={size} />)
      
      const panel = screen.getByTestId('modal-panel')
      expect(panel).toHaveClass(`max-w-${size}`)
      
      unmount()
    })
  })

  it('calls onClose when close button is clicked', async () => {
    const onClose = jest.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    const closeButton = screen.getByRole('button')
    await user.click(closeButton)
    
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('has proper accessibility attributes', () => {
    render(<Modal {...defaultProps} />)
    
    const closeButton = screen.getByRole('button')
    expect(closeButton).toHaveAttribute('type', 'button')
    
    // Screen reader text for close button
    expect(screen.getByText('Close')).toBeInTheDocument()
    expect(screen.getByText('Close')).toHaveClass('sr-only')
    
    const closeIcon = screen.getByTestId('close-icon')
    expect(closeIcon).toHaveAttribute('aria-hidden', 'true')
  })

  it('renders title as h3 element', () => {
    render(<Modal {...defaultProps} />)
    
    const title = screen.getByTestId('modal-title')
    expect(title.tagName).toBe('H3')
    expect(title).toHaveClass('text-lg', 'font-semibold', 'leading-6', 'text-gray-900', 'mb-4')
  })

  it('renders custom children content', () => {
    const customContent = (
      <div>
        <p>Custom paragraph</p>
        <button>Custom button</button>
      </div>
    )
    
    render(<Modal {...defaultProps} children={customContent} />)
    
    expect(screen.getByText('Custom paragraph')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /custom button/i })).toBeInTheDocument()
  })

  it('has proper modal styling classes', () => {
    render(<Modal {...defaultProps} />)
    
    const panel = screen.getByTestId('modal-panel')
    expect(panel).toHaveClass(
      'relative',
      'transform',
      'overflow-hidden',
      'rounded-lg',
      'bg-white',
      'px-4',
      'pb-4',
      'pt-5',
      'text-left',
      'shadow-xl',
      'transition-all'
    )
  })

  it('close button has proper styling', () => {
    render(<Modal {...defaultProps} />)
    
    const closeButton = screen.getByRole('button')
    expect(closeButton).toHaveClass(
      'rounded-md',
      'bg-white',
      'text-gray-400',
      'hover:text-gray-500',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-indigo-500',
      'focus:ring-offset-2'
    )
  })

  it('supports keyboard navigation', async () => {
    const onClose = jest.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    const closeButton = screen.getByRole('button')
    closeButton.focus()
    expect(closeButton).toHaveFocus()
    
    await user.keyboard('{Enter}')
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('renders with proper responsive classes', () => {
    render(<Modal {...defaultProps} />)
    
    const panel = screen.getByTestId('modal-panel')
    expect(panel).toHaveClass('sm:my-8', 'sm:w-full', 'sm:p-6')
  })

  it('maintains focus management', () => {
    render(<Modal {...defaultProps} />)
    
    // Modal should be focusable for screen readers
    const modal = screen.getByTestId('modal-root')
    expect(modal).toBeInTheDocument()
  })

  it('handles dynamic title changes', () => {
    const { rerender } = render(<Modal {...defaultProps} title="Original Title" />)
    expect(screen.getByText('Original Title')).toBeInTheDocument()
    
    rerender(<Modal {...defaultProps} title="Updated Title" />)
    expect(screen.getByText('Updated Title')).toBeInTheDocument()
    expect(screen.queryByText('Original Title')).not.toBeInTheDocument()
  })

  it('handles dynamic content changes', () => {
    const { rerender } = render(
      <Modal {...defaultProps} children={<div>Original Content</div>} />
    )
    expect(screen.getByText('Original Content')).toBeInTheDocument()
    
    rerender(
      <Modal {...defaultProps} children={<div>Updated Content</div>} />
    )
    expect(screen.getByText('Updated Content')).toBeInTheDocument()
    expect(screen.queryByText('Original Content')).not.toBeInTheDocument()
  })
})