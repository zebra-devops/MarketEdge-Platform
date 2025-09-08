/**
 * Accessibility testing utilities
 * 
 * Provides utilities for automated accessibility testing across the platform
 */

import { render, RenderResult } from '@testing-library/react'
import { axe, AxeResults, toHaveNoViolations } from 'jest-axe'
import { ReactElement } from 'react'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

/**
 * WCAG 2.1 AA compliance configuration for axe-core
 */
export const wcagConfig = {
  rules: {
    // Color contrast rules
    'color-contrast': { enabled: true },
    'color-contrast-enhanced': { enabled: true },
    
    // Keyboard accessibility
    'keyboard': { enabled: true },
    'focus-order-semantics': { enabled: true },
    'tabindex': { enabled: true },
    
    // Screen reader compatibility
    'aria-allowed-attr': { enabled: true },
    'aria-command-name': { enabled: true },
    'aria-hidden-body': { enabled: true },
    'aria-hidden-focus': { enabled: true },
    'aria-input-field-name': { enabled: true },
    'aria-label': { enabled: true },
    'aria-labelledby': { enabled: true },
    'aria-required-attr': { enabled: true },
    'aria-required-children': { enabled: true },
    'aria-required-parent': { enabled: true },
    'aria-roles': { enabled: true },
    'aria-valid-attr': { enabled: true },
    'aria-valid-attr-value': { enabled: true },
    
    // Form accessibility
    'form-field-multiple-labels': { enabled: true },
    'label': { enabled: true },
    'label-content-name-mismatch': { enabled: true },
    'label-title-only': { enabled: true },
    
    // Image accessibility
    'image-alt': { enabled: true },
    'image-redundant-alt': { enabled: true },
    
    // Link accessibility
    'link-name': { enabled: true },
    'link-in-text-block': { enabled: true },
    
    // Button accessibility
    'button-name': { enabled: true },
    
    // Table accessibility
    'table-duplicate-name': { enabled: true },
    'table-fake-caption': { enabled: true },
    'td-headers-attr': { enabled: true },
    'th-has-data-cells': { enabled: true },
    
    // Landmark and structure
    'landmark-one-main': { enabled: true },
    'landmark-complementary-is-top-level': { enabled: true },
    'landmark-contentinfo-is-top-level': { enabled: true },
    'landmark-main-is-top-level': { enabled: true },
    'landmark-no-duplicate-banner': { enabled: true },
    'landmark-no-duplicate-contentinfo': { enabled: true },
    'landmark-no-duplicate-main': { enabled: true },
    'page-has-heading-one': { enabled: true },
    'region': { enabled: true },
    
    // Document structure
    'document-title': { enabled: true },
    'html-has-lang': { enabled: true },
    'html-lang-valid': { enabled: true },
    'html-xml-lang-mismatch': { enabled: true },
    
    // Focus management
    'focus-order-semantics': { enabled: true },
    'focusable-content': { enabled: true },
    'no-focusable-content': { enabled: true },
    
    // Skip navigation
    'skip-link': { enabled: true },
  },
  tags: ['wcag2a', 'wcag2aa', 'wcag21aa', 'section508']
}

/**
 * Test a component for accessibility violations
 */
export async function testAccessibility(
  component: ReactElement,
  options: {
    config?: any;
    renderOptions?: any;
    skipRules?: string[];
  } = {}
): Promise<AxeResults> {
  const { config = wcagConfig, renderOptions = {}, skipRules = [] } = options
  
  const { container } = render(component, renderOptions)
  
  // Apply rule exclusions
  const finalConfig = { ...config }
  if (skipRules.length > 0) {
    finalConfig.rules = { ...config.rules }
    skipRules.forEach(rule => {
      if (finalConfig.rules[rule]) {
        finalConfig.rules[rule] = { enabled: false }
      }
    })
  }
  
  const results = await axe(container, finalConfig)
  return results
}

/**
 * Assert that a component has no accessibility violations
 */
export async function expectNoAccessibilityViolations(
  component: ReactElement,
  options: {
    config?: any;
    renderOptions?: any;
    skipRules?: string[];
  } = {}
): Promise<void> {
  const results = await testAccessibility(component, options)
  expect(results).toHaveNoViolations()
}

/**
 * Test keyboard navigation for a component
 */
export async function testKeyboardNavigation(
  component: ReactElement,
  testScenarios: {
    description: string;
    keys: string[];
    expectedFocus?: string;
    expectedAction?: () => void;
  }[]
): Promise<void> {
  const { render, screen } = await import('@testing-library/react')
  const userEvent = (await import('@testing-library/user-event')).default
  
  render(component)
  const user = userEvent.setup()
  
  for (const scenario of testScenarios) {
    for (const key of scenario.keys) {
      await user.keyboard(key)
    }
    
    if (scenario.expectedFocus) {
      const focusedElement = screen.getByRole(scenario.expectedFocus)
      expect(focusedElement).toHaveFocus()
    }
    
    if (scenario.expectedAction) {
      scenario.expectedAction()
    }
  }
}

/**
 * Test screen reader compatibility
 */
export async function testScreenReaderCompatibility(
  component: ReactElement
): Promise<{
  landmarks: string[];
  headings: string[];
  labels: string[];
  descriptions: string[];
}> {
  const { render, screen } = await import('@testing-library/react')
  
  render(component)
  
  // Find all landmarks
  const landmarks = screen.queryAllByRole('region')
    .concat(screen.queryAllByRole('main'))
    .concat(screen.queryAllByRole('navigation'))
    .concat(screen.queryAllByRole('banner'))
    .concat(screen.queryAllByRole('contentinfo'))
    .concat(screen.queryAllByRole('complementary'))
    .map(el => el.getAttribute('aria-label') || el.textContent?.slice(0, 50) || 'Unlabeled landmark')
  
  // Find all headings
  const headings = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    .flatMap(tag => Array.from(document.querySelectorAll(tag)))
    .map(el => el.textContent || 'Empty heading')
  
  // Find all form labels
  const labels = Array.from(document.querySelectorAll('label'))
    .map(el => el.textContent || 'Empty label')
  
  // Find all descriptions (aria-describedby)
  const descriptions = Array.from(document.querySelectorAll('[aria-describedby]'))
    .map(el => {
      const describedBy = el.getAttribute('aria-describedby')
      const descElement = document.getElementById(describedBy || '')
      return descElement?.textContent || 'Missing description'
    })
  
  return {
    landmarks,
    headings,
    labels,
    descriptions
  }
}

/**
 * Test color contrast compliance
 */
export async function testColorContrast(
  component: ReactElement,
  options: {
    skipElements?: string[];
    minimumRatio?: number;
  } = {}
): Promise<AxeResults> {
  const { skipElements = [], minimumRatio = 4.5 } = options
  
  const contrastConfig = {
    rules: {
      'color-contrast': { 
        enabled: true,
        options: {
          noScroll: true,
          ignoreUseReady: true,
          ...(minimumRatio !== 4.5 && { 
            contrastRatio: { normal: { aa: minimumRatio } }
          })
        }
      }
    },
    tags: ['wcag2aa'],
    ...(skipElements.length > 0 && {
      exclude: skipElements
    })
  }
  
  return testAccessibility(component, { config: contrastConfig })
}

/**
 * Test form accessibility
 */
export async function testFormAccessibility(
  component: ReactElement
): Promise<{
  violations: AxeResults;
  formElements: {
    inputs: number;
    labels: number;
    fieldsets: number;
    legends: number;
    errors: number;
    required: number;
  };
}> {
  const { render } = await import('@testing-library/react')
  
  const { container } = render(component)
  
  // Count form elements
  const formElements = {
    inputs: container.querySelectorAll('input, textarea, select').length,
    labels: container.querySelectorAll('label').length,
    fieldsets: container.querySelectorAll('fieldset').length,
    legends: container.querySelectorAll('legend').length,
    errors: container.querySelectorAll('[aria-invalid="true"], [role="alert"]').length,
    required: container.querySelectorAll('[required], [aria-required="true"]').length,
  }
  
  // Test form-specific accessibility
  const formConfig = {
    rules: {
      'label': { enabled: true },
      'label-title-only': { enabled: true },
      'label-content-name-mismatch': { enabled: true },
      'form-field-multiple-labels': { enabled: true },
      'aria-input-field-name': { enabled: true },
      'aria-required-attr': { enabled: true },
      'aria-required-children': { enabled: true },
    },
    tags: ['wcag2a', 'wcag2aa']
  }
  
  const violations = await axe(container, formConfig)
  
  return {
    violations,
    formElements
  }
}

/**
 * Generate accessibility report
 */
export function generateAccessibilityReport(
  results: AxeResults,
  componentName: string
): string {
  const { violations, passes, incomplete } = results
  
  let report = `\n=== Accessibility Report for ${componentName} ===\n`
  report += `✅ Passed: ${passes.length} rules\n`
  report += `❌ Violations: ${violations.length} rules\n`
  report += `⚠️  Incomplete: ${incomplete.length} rules\n\n`
  
  if (violations.length > 0) {
    report += `VIOLATIONS:\n`
    violations.forEach((violation, index) => {
      report += `${index + 1}. ${violation.id} (${violation.impact})\n`
      report += `   ${violation.description}\n`
      report += `   Help: ${violation.helpUrl}\n`
      report += `   Elements: ${violation.nodes.length}\n\n`
    })
  }
  
  if (incomplete.length > 0) {
    report += `INCOMPLETE (Manual Review Needed):\n`
    incomplete.forEach((item, index) => {
      report += `${index + 1}. ${item.id}\n`
      report += `   ${item.description}\n`
      report += `   Elements: ${item.nodes.length}\n\n`
    })
  }
  
  return report
}

/**
 * Common accessibility test suite for components
 */
export function createAccessibilityTestSuite(
  componentName: string,
  component: ReactElement,
  options: {
    skipRules?: string[];
    testKeyboard?: boolean;
    testScreenReader?: boolean;
    testColorContrast?: boolean;
    testForms?: boolean;
  } = {}
) {
  const {
    skipRules = [],
    testKeyboard = true,
    testScreenReader = true,
    testColorContrast = true,
    testForms = false
  } = options

  describe(`${componentName} Accessibility`, () => {
    it('has no WCAG 2.1 AA violations', async () => {
      await expectNoAccessibilityViolations(component, { skipRules })
    })

    if (testColorContrast) {
      it('meets color contrast requirements', async () => {
        const results = await testColorContrast(component)
        expect(results).toHaveNoViolations()
      })
    }

    if (testScreenReader) {
      it('provides proper screen reader support', async () => {
        const srInfo = await testScreenReaderCompatibility(component)
        
        // Basic assertions - adjust based on component needs
        expect(srInfo.headings.length).toBeGreaterThan(0)
        expect(srInfo.landmarks.length).toBeGreaterThan(0)
      })
    }

    if (testForms) {
      it('has accessible form elements', async () => {
        const { violations, formElements } = await testFormAccessibility(component)
        
        expect(violations).toHaveNoViolations()
        expect(formElements.inputs).toBeGreaterThan(0)
        expect(formElements.labels).toBe(formElements.inputs) // All inputs should have labels
      })
    }
  })
}