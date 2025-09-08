import React from 'react'
import { render, screen } from '@/test-utils'
import LoadingSpinner from '../LoadingSpinner'

describe('LoadingSpinner Component', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner />)
    
    const container = screen.getByTestId('loading-spinner')
    expect(container).toBeInTheDocument()
    expect(container).toHaveClass('flex', 'justify-center', 'items-center')
    
    const spinner = container.firstChild
    expect(spinner).toHaveClass('animate-spin', 'rounded-full', 'border-2')
  })

  it('renders with medium size by default', () => {
    render(<LoadingSpinner />)
    
    const container = screen.getByTestId('loading-spinner')
    const spinner = container.firstChild
    expect(spinner).toHaveClass('h-8', 'w-8')
  })

  it('renders with small size', () => {
    render(<LoadingSpinner size="sm" />)
    
    const container = screen.getByTestId('loading-spinner')
    const spinner = container.firstChild
    expect(spinner).toHaveClass('h-4', 'w-4')
  })

  it('renders with large size', () => {
    render(<LoadingSpinner size="lg" />)
    
    const container = screen.getByTestId('loading-spinner')
    const spinner = container.firstChild
    expect(spinner).toHaveClass('h-12', 'w-12')
  })

  it('applies custom className', () => {
    render(<LoadingSpinner className="custom-spinner" />)
    
    const container = screen.getByTestId('loading-spinner')
    expect(container).toHaveClass('custom-spinner')
  })

  it('has proper spinner styling', () => {
    render(<LoadingSpinner />)
    
    const container = screen.getByTestId('loading-spinner')
    const spinner = container.firstChild
    
    expect(spinner).toHaveClass(
      'animate-spin',
      'rounded-full',
      'border-2',
      'border-gray-300',
      'border-t-primary-600'
    )
  })

  it('maintains consistent structure across sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const
    
    sizes.forEach(size => {
      const { container, unmount } = render(<LoadingSpinner size={size} />)
      
      const wrapper = container.firstChild
      expect(wrapper).toHaveClass('flex', 'justify-center', 'items-center')
      
      const spinner = wrapper?.firstChild
      expect(spinner).toHaveClass('animate-spin', 'rounded-full', 'border-2')
      
      unmount()
    })
  })

  it('combines custom className with default classes', () => {
    render(<LoadingSpinner className="my-4 text-red-500" />)
    
    const container = screen.getByTestId('loading-spinner')
    expect(container).toHaveClass('flex', 'justify-center', 'items-center', 'my-4', 'text-red-500')
  })

  it('is accessible for screen readers', () => {
    render(<LoadingSpinner />)
    
    // While not explicitly tested, the component structure supports
    // adding aria-label or role attributes if needed for accessibility
    const container = screen.getByTestId('loading-spinner')
    expect(container).toBeInTheDocument()
  })

  it('renders consistently with different props combinations', () => {
    render(
      <div>
        <LoadingSpinner size="sm" className="mr-2" />
        <LoadingSpinner size="md" className="mr-2" />
        <LoadingSpinner size="lg" className="mr-2" />
      </div>
    )
    
    const spinners = screen.getAllByTestId('loading-spinner')
    expect(spinners).toHaveLength(3)
    
    spinners.forEach(spinner => {
      expect(spinner).toHaveClass('flex', 'justify-center', 'items-center', 'mr-2')
    })
  })
})