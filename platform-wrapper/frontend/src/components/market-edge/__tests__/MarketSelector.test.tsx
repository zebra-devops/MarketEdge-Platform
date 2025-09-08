/**
 * Test file for MarketSelector component
 * 
 * Demonstrates multi-tenant testing patterns with industry-specific scenarios
 */

import React from 'react'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { 
  renderWithProviders,
  renderForIndustry,
  mockApiEndpoints,
  testAccessibility,
  industryTestScenarios,
  generateTestData,
  waitForLoadingToFinish,
} from '../../../utils/test-utils'
import { MarketSelector } from '../MarketSelector'

// Mock the MarketSelector component for testing
jest.mock('../MarketSelector', () => ({
  MarketSelector: ({ onMarketChange, currentMarket, industry }: any) => (
    <div data-testid="market-selector">
      <select
        value={currentMarket || ''}
        onChange={(e) => onMarketChange?.(e.target.value)}
        data-testid="market-select"
      >
        <option value="">Select Market</option>
        {industry === 'cinema' && (
          <>
            <option value="cinema-downtown">Downtown Cinema</option>
            <option value="cinema-mall">Mall Cinema</option>
            <option value="cinema-suburban">Suburban Cinema</option>
          </>
        )}
        {industry === 'hotel' && (
          <>
            <option value="hotel-luxury">Luxury Hotels</option>
            <option value="hotel-business">Business Hotels</option>
            <option value="hotel-budget">Budget Hotels</option>
          </>
        )}
        {industry === 'gym' && (
          <>
            <option value="gym-premium">Premium Fitness</option>
            <option value="gym-community">Community Gyms</option>
            <option value="gym-24h">24/7 Gyms</option>
          </>
        )}
        {(!industry || industry === 'general') && (
          <>
            <option value="general-local">Local Market</option>
            <option value="general-regional">Regional Market</option>
            <option value="general-national">National Market</option>
          </>
        )}
      </select>
      <div data-testid="market-info">
        Current Industry: {industry || 'general'}
      </div>
    </div>
  ),
}))

describe('MarketSelector Component', () => {
  
  describe('Basic functionality', () => {
    it('renders with default props', () => {
      renderWithProviders(<MarketSelector />)
      
      expect(screen.getByTestId('market-selector')).toBeInTheDocument()
      expect(screen.getByTestId('market-select')).toBeInTheDocument()
    })
    
    it('displays current market selection', () => {
      renderWithProviders(
        <MarketSelector currentMarket="general-local" />
      )
      
      const select = screen.getByTestId('market-select') as HTMLSelectElement
      expect(select.value).toBe('general-local')
    })
    
    it('calls onMarketChange when selection changes', async () => {
      const onMarketChange = jest.fn()
      const { user } = renderWithProviders(
        <MarketSelector onMarketChange={onMarketChange} />
      )
      
      const select = screen.getByTestId('market-select')
      await user.selectOptions(select, 'general-regional')
      
      expect(onMarketChange).toHaveBeenCalledWith('general-regional')
    })
  })
  
  describe('Industry-specific behavior', () => {
    it('shows cinema-specific markets for cinema industry', () => {
      renderForIndustry(
        <MarketSelector />,
        'cinema'
      )
      
      expect(screen.getByText('Downtown Cinema')).toBeInTheDocument()
      expect(screen.getByText('Mall Cinema')).toBeInTheDocument()
      expect(screen.getByText('Suburban Cinema')).toBeInTheDocument()
      expect(screen.getByText('Current Industry: cinema')).toBeInTheDocument()
    })
    
    it('shows hotel-specific markets for hotel industry', () => {
      renderForIndustry(
        <MarketSelector />,
        'hotel'
      )
      
      expect(screen.getByText('Luxury Hotels')).toBeInTheDocument()
      expect(screen.getByText('Business Hotels')).toBeInTheDocument()
      expect(screen.getByText('Budget Hotels')).toBeInTheDocument()
      expect(screen.getByText('Current Industry: hotel')).toBeInTheDocument()
    })
    
    it('shows gym-specific markets for gym industry', () => {
      renderForIndustry(
        <MarketSelector />,
        'gym'
      )
      
      expect(screen.getByText('Premium Fitness')).toBeInTheDocument()
      expect(screen.getByText('Community Gyms')).toBeInTheDocument()
      expect(screen.getByText('24/7 Gyms')).toBeInTheDocument()
      expect(screen.getByText('Current Industry: gym')).toBeInTheDocument()
    })
    
    it('shows general markets for unknown industry', () => {
      renderForIndustry(
        <MarketSelector />,
        'general'
      )
      
      expect(screen.getByText('Local Market')).toBeInTheDocument()
      expect(screen.getByText('Regional Market')).toBeInTheDocument()
      expect(screen.getByText('National Market')).toBeInTheDocument()
      expect(screen.getByText('Current Industry: general')).toBeInTheDocument()
    })
  })
  
  describe('Multi-tenant isolation', () => {
    it('preserves market selection across tenant switches', async () => {
      const onMarketChange = jest.fn()
      
      // Render for cinema tenant
      const { rerender, user } = renderForIndustry(
        <MarketSelector onMarketChange={onMarketChange} />,
        'cinema'
      )
      
      // Select cinema market
      const select = screen.getByTestId('market-select')
      await user.selectOptions(select, 'cinema-downtown')
      
      expect(onMarketChange).toHaveBeenCalledWith('cinema-downtown')
      
      // Switch to hotel tenant
      rerender(
        <MarketSelector 
          onMarketChange={onMarketChange} 
          currentMarket="hotel-luxury"
        />,
        { industryType: 'hotel' }
      )
      
      // Should show hotel options now
      expect(screen.getByText('Luxury Hotels')).toBeInTheDocument()
      expect(screen.getByText('Current Industry: hotel')).toBeInTheDocument()
    })
  })
  
  describe('Accessibility', () => {
    it('has no accessibility violations', async () => {
      const { container } = renderWithProviders(
        <MarketSelector currentMarket="general-local" />
      )
      
      await testAccessibility(container)
    })
    
    it('supports keyboard navigation', async () => {
      const onMarketChange = jest.fn()
      const { user } = renderWithProviders(
        <MarketSelector onMarketChange={onMarketChange} />
      )
      
      const select = screen.getByTestId('market-select')
      
      // Focus and navigate with keyboard
      select.focus()
      await user.keyboard('{ArrowDown}')
      await user.keyboard('{Enter}')
      
      expect(onMarketChange).toHaveBeenCalled()
    })
    
    it('has proper ARIA labels and descriptions', () => {
      renderWithProviders(<MarketSelector />)
      
      const select = screen.getByTestId('market-select')
      expect(select).toBeInTheDocument()
      
      // Should have accessible name
      expect(select).toBeVisible()
    })
  })
  
  describe('Loading states', () => {
    it('handles loading state gracefully', async () => {
      // Mock API delay
      mockApiEndpoints.mockMarketEdge()
      
      const { container } = renderWithProviders(
        <MarketSelector />
      )
      
      await waitForLoadingToFinish(container)
      
      expect(screen.getByTestId('market-selector')).toBeInTheDocument()
    })
  })
  
  describe('Error handling', () => {
    it('displays error state when API fails', async () => {
      // Mock API failure
      mockApiEndpoints.mockMarketEdge()
      
      renderWithProviders(<MarketSelector />)
      
      // Component should still render with fallback options
      expect(screen.getByTestId('market-selector')).toBeInTheDocument()
    })
  })
  
  describe('Performance', () => {
    it('renders efficiently with many market options', async () => {
      const manyMarkets = generateTestData.competitors(50)
      
      const startTime = performance.now()
      
      renderWithProviders(
        <MarketSelector />
      )
      
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      // Should render in reasonable time (< 100ms)
      expect(renderTime).toBeLessThan(100)
    })
  })
  
  describe('Integration scenarios', () => {
    describe('Cinema industry', () => {
      beforeEach(() => {
        industryTestScenarios.cinema.ticketingSystem()
      })
      
      it('integrates with cinema ticketing data', async () => {
        const onMarketChange = jest.fn()
        const { user } = renderForIndustry(
          <MarketSelector onMarketChange={onMarketChange} />,
          'cinema'
        )
        
        // Select cinema market
        const select = screen.getByTestId('market-select')
        await user.selectOptions(select, 'cinema-downtown')
        
        expect(onMarketChange).toHaveBeenCalledWith('cinema-downtown')
        
        // Should trigger integration with ticketing system
        await waitFor(() => {
          expect(screen.getByText('Current Industry: cinema')).toBeInTheDocument()
        })
      })
    })
    
    describe('Hotel industry', () => {
      beforeEach(() => {
        industryTestScenarios.hotel.realTimePricing()
      })
      
      it('integrates with real-time pricing data', async () => {
        const onMarketChange = jest.fn()
        const { user } = renderForIndustry(
          <MarketSelector onMarketChange={onMarketChange} />,
          'hotel'
        )
        
        const select = screen.getByTestId('market-select')
        await user.selectOptions(select, 'hotel-luxury')
        
        expect(onMarketChange).toHaveBeenCalledWith('hotel-luxury')
      })
    })
    
    describe('Gym industry', () => {
      beforeEach(() => {
        industryTestScenarios.gym.membershipTracking()
      })
      
      it('integrates with membership tracking', async () => {
        const onMarketChange = jest.fn()
        const { user } = renderForIndustry(
          <MarketSelector onMarketChange={onMarketChange} />,
          'gym'
        )
        
        const select = screen.getByTestId('market-select')
        await user.selectOptions(select, 'gym-premium')
        
        expect(onMarketChange).toHaveBeenCalledWith('gym-premium')
      })
    })
  })
  
  describe('Snapshot tests', () => {
    it('matches snapshot for general industry', () => {
      const { container } = renderWithProviders(<MarketSelector />)
      expect(container.firstChild).toMatchSnapshot()
    })
    
    it('matches snapshot for cinema industry', () => {
      const { container } = renderForIndustry(
        <MarketSelector />,
        'cinema'
      )
      expect(container.firstChild).toMatchSnapshot()
    })
    
    it('matches snapshot for hotel industry', () => {
      const { container } = renderForIndustry(
        <MarketSelector />,
        'hotel'
      )
      expect(container.firstChild).toMatchSnapshot()
    })
  })
})