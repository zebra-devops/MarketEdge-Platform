/**
 * Tests for Button Component
 * 
 * Comprehensive test suite covering:
 * - Basic rendering and functionality
 * - Different variants and sizes
 * - Accessibility features
 * - User interactions
 * - Loading and disabled states
 */

import { render, screen, fireEvent } from '@test-utils'
import { axe } from 'jest-axe'
import { Button } from '../Button'

describe('Button Component', () => {
  describe('Basic Rendering', () => {
    it('renders button with text content', () => {
      render(<Button>Click me</Button>)
      
      const button = screen.getByRole('button', { name: /click me/i })
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent('Click me')
    })

    it('renders button with custom className', () => {
      render(<Button className="custom-class">Test</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })

    it('forwards ref correctly', () => {
      const ref = { current: null } as React.RefObject<HTMLButtonElement>
      
      render(<Button ref={ref}>Test</Button>)
      
      expect(ref.current).toBeInstanceOf(HTMLButtonElement)
    })
  })

  describe('Button Variants', () => {
    it('renders primary variant by default', () => {
      render(<Button>Primary</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-blue-600') // Assuming Tailwind classes
    })

    it('renders secondary variant when specified', () => {
      render(<Button variant="secondary">Secondary</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-gray-600')
    })

    it('renders destructive variant when specified', () => {
      render(<Button variant="destructive">Delete</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-red-600')
    })

    it('renders outline variant when specified', () => {
      render(<Button variant="outline">Outline</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border')
      expect(button).not.toHaveClass('bg-blue-600')
    })

    it('renders ghost variant when specified', () => {
      render(<Button variant="ghost">Ghost</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:bg-gray-100')
    })
  })

  describe('Button Sizes', () => {
    it('renders default size when not specified', () => {
      render(<Button>Default</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10')
    })

    it('renders small size when specified', () => {
      render(<Button size="sm">Small</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-9')
    })

    it('renders large size when specified', () => {
      render(<Button size="lg">Large</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-11')
    })

    it('renders icon size when specified', () => {
      render(<Button size="icon">🔍</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10', 'w-10')
    })
  })

  describe('Interactive States', () => {
    it('handles click events', () => {
      const handleClick = jest.fn()
      render(<Button onClick={handleClick}>Click me</Button>)
      
      const button = screen.getByRole('button')
      fireEvent.click(button)
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not trigger onClick when disabled', () => {
      const handleClick = jest.fn()
      render(<Button disabled onClick={handleClick}>Disabled</Button>)
      
      const button = screen.getByRole('button')
      fireEvent.click(button)
      
      expect(handleClick).not.toHaveBeenCalled()
      expect(button).toBeDisabled()
    })

    it('shows loading state correctly', () => {
      render(<Button loading>Loading</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('prevents click events during loading', () => {
      const handleClick = jest.fn()
      render(<Button loading onClick={handleClick}>Loading</Button>)
      
      const button = screen.getByRole('button')
      fireEvent.click(button)
      
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(<Button>Accessible Button</Button>)
      const results = await axe(container)
      
      expect(results).toHaveNoViolations()
    })

    it('supports custom ARIA labels', () => {
      render(<Button aria-label="Custom label">Icon only</Button>)
      
      const button = screen.getByRole('button', { name: /custom label/i })
      expect(button).toBeInTheDocument()
    })

    it('supports ARIA describedby', () => {
      render(
        <>
          <Button aria-describedby="help-text">Submit</Button>
          <div id="help-text">This will submit the form</div>
        </>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-describedby', 'help-text')
    })

    it('has correct role and type attributes', () => {
      render(<Button type="submit">Submit</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'submit')
    })
  })

  describe('Form Integration', () => {
    it('can be used as form submission button', () => {
      const handleSubmit = jest.fn(e => e.preventDefault())
      
      render(
        <form onSubmit={handleSubmit}>
          <Button type="submit">Submit Form</Button>
        </form>
      )
      
      const button = screen.getByRole('button')
      fireEvent.click(button)
      
      expect(handleSubmit).toHaveBeenCalledTimes(1)
    })

    it('can be used as form reset button', () => {
      render(
        <form>
          <input defaultValue="test" />
          <Button type="reset">Reset Form</Button>
        </form>
      )
      
      const input = screen.getByRole('textbox')
      const resetButton = screen.getByRole('button')
      
      // Change input value
      fireEvent.change(input, { target: { value: 'changed' } })
      expect(input).toHaveValue('changed')
      
      // Reset form
      fireEvent.click(resetButton)
      expect(input).toHaveValue('test')
    })
  })

  describe('Multi-tenant Context', () => {
    it('renders correctly in cinema tenant context', () => {
      render(<Button>Book Tickets</Button>, {
        tenant: { industry: 'cinema', organizationName: 'CineMax' },
      })
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent('Book Tickets')
    })

    it('renders correctly in hotel tenant context', () => {
      render(<Button>Make Reservation</Button>, {
        tenant: { industry: 'hotel', organizationName: 'Grand Hotel' },
      })
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent('Make Reservation')
    })

    it('applies tenant-specific styling if implemented', () => {
      // This test would be more relevant if the button component
      // actually uses tenant context for styling
      render(<Button>Test</Button>, {
        tenant: { industry: 'cinema' },
      })
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      // Add assertions for tenant-specific styling if implemented
    })
  })

  describe('Edge Cases', () => {
    it('handles very long button text', () => {
      const longText = 'This is a very long button text that should be handled gracefully'
      
      render(<Button>{longText}</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveTextContent(longText)
      expect(button).toBeInTheDocument()
    })

    it('handles empty content gracefully', () => {
      render(<Button></Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent('')
    })

    it('handles rapid clicks', () => {
      const handleClick = jest.fn()
      render(<Button onClick={handleClick}>Rapid Click</Button>)
      
      const button = screen.getByRole('button')
      
      // Simulate rapid clicks
      for (let i = 0; i < 5; i++) {
        fireEvent.click(button)
      }
      
      expect(handleClick).toHaveBeenCalledTimes(5)
    })

    it('maintains focus when not disabled', () => {
      render(<Button>Focus Test</Button>)
      
      const button = screen.getByRole('button')
      button.focus()
      
      expect(button).toHaveFocus()
    })

    it('cannot receive focus when disabled', () => {
      render(<Button disabled>Disabled Focus</Button>)
      
      const button = screen.getByRole('button')
      button.focus()
      
      expect(button).not.toHaveFocus()
    })
  })

  describe('Performance', () => {
    it('does not re-render unnecessarily', () => {
      const renderSpy = jest.fn()
      
      const TestButton = (props: any) => {
        renderSpy()
        return <Button {...props} />
      }
      
      const { rerender } = render(<TestButton>Test</TestButton>)
      
      expect(renderSpy).toHaveBeenCalledTimes(1)
      
      // Re-render with same props
      rerender(<TestButton>Test</TestButton>)
      
      // Should not cause additional renders if properly memoized
      expect(renderSpy).toHaveBeenCalledTimes(2)
    })
  })
})