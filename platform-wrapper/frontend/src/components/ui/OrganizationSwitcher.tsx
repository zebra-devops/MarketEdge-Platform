'use client'

import { Fragment, useState } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import {
  BuildingOfficeIcon,
  ChevronDownIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import { Organisation } from '@/types/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const getIndustryIcon = (industry: string) => {
  // Industry badge colors and icons
  switch (industry.toLowerCase()) {
    case 'cinema exhibition':
    case 'cinema':
      return { color: 'bg-purple-100 text-purple-800', icon: '🎬' }
    case 'hotel':
    case 'accommodation':
      return { color: 'bg-blue-100 text-blue-800', icon: '🏨' }
    case 'gym':
    case 'fitness':
      return { color: 'bg-green-100 text-green-800', icon: '💪' }
    case 'retail':
    case 'retail trade':
      return { color: 'bg-yellow-100 text-yellow-800', icon: '🛍️' }
    case 'b2b':
    case 'business services':
      return { color: 'bg-gray-100 text-gray-800', icon: '🏢' }
    default:
      return { color: 'bg-gray-100 text-gray-800', icon: '🏢' }
  }
}

interface OrganizationSwitcherProps {
  className?: string
}

export default function OrganizationSwitcher({ className = '' }: OrganizationSwitcherProps) {
  const {
    currentOrganisation,
    accessibleOrganisations,
    switchOrganisation,
    isSwitching,
    isLoadingAccessible,
    isSuperAdmin,
  } = useOrganisationContext()

  const [isOpen, setIsOpen] = useState(false)

  const handleSwitchOrganisation = async (organisation: Organisation) => {
    if (organisation.id === currentOrganisation?.id || isSwitching) return
    
    try {
      await switchOrganisation(organisation.id)
      setIsOpen(false)
    } catch (error) {
      console.error('Failed to switch organization:', error)
      // Error handling could show a toast notification here
    }
  }

  // Don't show if user has access to only one organization or none
  // Exception: Show for super admins even if they only have one org, as they can potentially access all
  if (isLoadingAccessible || (accessibleOrganisations.length <= 1 && !isSuperAdmin)) {
    return null
  }

  // For super admins, show even if only one org is loaded (they can access others)
  if (isSuperAdmin && accessibleOrganisations.length === 0) {
    return null
  }

  const currentOrgDisplay = currentOrganisation || accessibleOrganisations[0]
  const currentIndustryStyle = getIndustryIcon(currentOrgDisplay?.industry || '')

  return (
    <div className={`relative ${className}`}>
      <Listbox value={currentOrganisation} onChange={handleSwitchOrganisation}>
        <div className="relative">
          <Listbox.Button
            className="relative w-full min-w-[200px] cursor-pointer rounded-lg bg-white py-2 pl-3 pr-10 text-left border border-gray-300 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 sm:text-sm"
            disabled={isSwitching}
          >
            <div className="flex items-center gap-3">
              {isSwitching ? (
                <LoadingSpinner size="sm" />
              ) : (
                <BuildingOfficeIcon className="h-5 w-5 text-gray-400" />
              )}
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="block truncate font-medium text-gray-900">
                    {currentOrgDisplay?.name || 'Select Organization'}
                  </span>
                  {currentOrgDisplay?.industry && (
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${currentIndustryStyle.color}`}
                    >
                      <span>{currentIndustryStyle.icon}</span>
                      <span className="hidden sm:inline">
                        {currentOrgDisplay.industry}
                      </span>
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
              <ChevronDownIcon
                className="h-5 w-5 text-gray-400"
                aria-hidden="true"
              />
            </span>
          </Listbox.Button>
          
          <Transition
            show={isOpen}
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
            beforeEnter={() => setIsOpen(true)}
            afterLeave={() => setIsOpen(false)}
          >
            <Listbox.Options className="absolute z-50 mt-1 max-h-60 w-full min-w-[280px] overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
              <div className="px-3 py-2 text-xs font-medium text-gray-500 border-b border-gray-200">
                {isSuperAdmin ? (
                  <div className="flex items-center justify-between">
                    <span>Switch Organization</span>
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                      Super Admin
                    </span>
                  </div>
                ) : (
                  'Switch Organization'
                )}
              </div>
              
              {accessibleOrganisations.map((organisation) => {
                const industryStyle = getIndustryIcon(organisation.industry || '')
                const isCurrent = organisation.id === currentOrganisation?.id
                
                return (
                  <Listbox.Option
                    key={organisation.id}
                    className={({ active, selected }) =>
                      `relative cursor-pointer select-none py-3 px-3 ${
                        active || selected
                          ? 'bg-primary-50 text-primary-900'
                          : 'text-gray-900'
                      } ${isCurrent ? 'bg-primary-50' : ''}`
                    }
                    value={organisation}
                  >
                    {({ selected }) => (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <BuildingOfficeIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`block truncate ${isCurrent ? 'font-semibold' : 'font-medium'}`}>
                                {organisation.name}
                              </span>
                              {isCurrent && (
                                <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                                  Current
                                </span>
                              )}
                            </div>
                            
                            {organisation.industry && (
                              <div className="flex items-center gap-2">
                                <span
                                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${industryStyle.color}`}
                                >
                                  <span>{industryStyle.icon}</span>
                                  <span>{organisation.industry}</span>
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {isCurrent && (
                          <CheckIcon className="h-5 w-5 text-primary-600" />
                        )}
                      </div>
                    )}
                  </Listbox.Option>
                )
              })}
            </Listbox.Options>
          </Transition>
        </div>
      </Listbox>
    </div>
  )
}