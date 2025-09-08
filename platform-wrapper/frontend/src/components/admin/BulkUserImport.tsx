'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import { apiService } from '@/services/api'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Modal from '@/components/ui/Modal'
import toast from 'react-hot-toast'
import { 
  DocumentArrowUpIcon,
  DocumentArrowDownIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ArrowPathIcon,
  EyeIcon,
  PlayIcon
} from '@heroicons/react/24/outline'

interface ImportPreviewData {
  email: string
  first_name: string
  last_name: string
  role: string
  department?: string
  location?: string
  phone?: string
  applications: {
    market_edge: boolean
    causal_edge: boolean
    value_edge: boolean
  }
}

interface ImportError {
  row: number
  field: string
  message: string
  value?: string
}

interface ImportDuplicate {
  row: number
  email: string
  message: string
  existing_user_id?: string
}

interface ImportPreviewResponse {
  is_valid: boolean
  total_rows: number
  valid_rows: number
  error_count: number
  duplicate_count: number
  warning_count: number
  errors: ImportError[]
  duplicates: ImportDuplicate[]
  warnings: any[]
  preview_data: ImportPreviewData[]
}

interface ImportBatchResponse {
  id: string
  filename: string
  status: string
  total_rows: number
  processed_rows: number
  successful_rows: number
  failed_rows: number
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

interface BulkUserImportProps {
  organisationId: string
  onImportComplete?: () => void
}

// Sanitize user input to prevent XSS attacks
const sanitizeHTML = (str: string): string => {
  if (!str) return ''
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

export default function BulkUserImport({ organisationId, onImportComplete }: BulkUserImportProps) {
  const { user: currentUser } = useAuthContext()
  const { allOrganisations } = useOrganisationContext()
  
  const [isOpen, setIsOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null)
  const [importBatch, setImportBatch] = useState<ImportBatchResponse | null>(null)
  const [sendInvitations, setSendInvitations] = useState(true)
  const [skipDuplicates, setSkipDuplicates] = useState(true)
  const [showPreview, setShowPreview] = useState(false)
  const [showErrors, setShowErrors] = useState(false)
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const currentOrg = allOrganisations?.find(org => org.id === organisationId)

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.csv')) {
        toast.error('Please select a CSV file')
        return
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error('File size must be less than 10MB')
        return
      }
      setSelectedFile(file)
      setPreviewData(null)
      setImportBatch(null)
    }
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file) {
      if (!file.name.endsWith('.csv')) {
        toast.error('Please select a CSV file')
        return
      }
      setSelectedFile(file)
      setPreviewData(null)
      setImportBatch(null)
    }
  }

  const downloadTemplate = async () => {
    try {
      const response = await fetch(`/api/v1/organizations/${organisationId}/users/import/template`, {
        headers: {
          'Authorization': `Bearer ${currentUser?.access_token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to download template')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'user_import_template.csv'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('Template downloaded successfully')
    } catch (error) {
      console.error('Failed to download template:', error)
      toast.error('Failed to download template')
    }
  }

  const validateFile = async () => {
    if (!selectedFile) return
    
    try {
      setIsValidating(true)
      
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      const response = await fetch(`/api/v1/organizations/${organisationId}/users/import/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentUser?.access_token}`,
        },
        body: formData,
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Validation failed')
      }
      
      const validationResult: ImportPreviewResponse = await response.json()
      setPreviewData(validationResult)
      
      if (validationResult.is_valid) {
        toast.success(`File validated successfully! ${validationResult.valid_rows} users ready for import`)
      } else {
        toast.error(`Validation failed with ${validationResult.error_count} errors`)
      }
    } catch (error: any) {
      console.error('Validation failed:', error)
      toast.error(error.message || 'File validation failed')
    } finally {
      setIsValidating(false)
    }
  }

  const executeImport = async () => {
    if (!selectedFile || !previewData?.is_valid) return
    
    try {
      setIsUploading(true)
      
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      const importRequest = {
        send_invitations: sendInvitations,
        skip_duplicates: skipDuplicates,
        default_role: 'viewer'
      }
      
      const response = await fetch(`/api/v1/organizations/${organisationId}/users/import?${new URLSearchParams({
        send_invitations: sendInvitations.toString(),
        skip_duplicates: skipDuplicates.toString(),
      })}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentUser?.access_token}`,
        },
        body: formData,
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Import failed')
      }
      
      const batchResult: ImportBatchResponse = await response.json()
      setImportBatch(batchResult)
      
      toast.success('Import started! Processing in background...')
      
      // Start polling for progress
      startProgressPolling(batchResult.id)
      
    } catch (error: any) {
      console.error('Import failed:', error)
      toast.error(error.message || 'Import failed')
    } finally {
      setIsUploading(false)
    }
  }

  const startProgressPolling = (batchId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiService.get<ImportBatchResponse>(
          `/organizations/${organisationId}/users/import/${batchId}`
        )
        setImportBatch(response)
        
        if (response.status === 'completed' || response.status === 'failed') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
          }
          
          if (response.status === 'completed') {
            toast.success(`Import completed! ${response.successful_rows} users created successfully`)
            if (onImportComplete) {
              onImportComplete()
            }
          } else {
            toast.error(`Import failed: ${response.error_message}`)
          }
        }
      } catch (error) {
        console.error('Failed to poll import status:', error)
      }
    }, 2000) // Poll every 2 seconds
  }

  const resetForm = () => {
    setSelectedFile(null)
    setPreviewData(null)
    setImportBatch(null)
    setShowPreview(false)
    setShowErrors(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }

  const handleClose = () => {
    resetForm()
    setIsOpen(false)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />
      case 'processing':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />
      default:
        return <ArrowPathIcon className="h-5 w-5 text-gray-500" />
    }
  }

  const getProgressPercentage = () => {
    if (!importBatch || importBatch.total_rows === 0) return 0
    return Math.round((importBatch.processed_rows / importBatch.total_rows) * 100)
  }

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        variant="secondary"
        className="flex items-center gap-2"
      >
        <DocumentArrowUpIcon className="h-5 w-5" />
        CSV Import
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={handleClose}
        title="Bulk User Import via CSV"
        maxWidth="4xl"
      >
        <div className="space-y-6">
          {/* Header Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-5 w-5 text-blue-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Importing to: {currentOrg?.name}
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>Upload a CSV file to bulk import users. Download the template to see the required format.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Download Template */}
          <div className="flex justify-between items-center">
            <Button
              onClick={downloadTemplate}
              variant="secondary"
              className="flex items-center gap-2"
            >
              <DocumentArrowDownIcon className="h-4 w-4" />
              Download Template
            </Button>
            
            <div className="space-y-2">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="send_invitations"
                  checked={sendInvitations}
                  onChange={(e) => setSendInvitations(e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="send_invitations" className="ml-2 text-sm text-gray-700">
                  Send invitation emails
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="skip_duplicates"
                  checked={skipDuplicates}
                  onChange={(e) => setSkipDuplicates(e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="skip_duplicates" className="ml-2 text-sm text-gray-700">
                  Skip duplicate emails
                </label>
              </div>
            </div>
          </div>

          {/* File Upload Area */}
          {!importBatch && (
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <p className="text-sm text-gray-600">
                  Drag and drop your CSV file here, or
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="secondary"
                  className="mt-2"
                >
                  Choose File
                </Button>
              </div>
              {selectedFile && (
                <div className="mt-4 text-sm text-gray-500">
                  Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
                </div>
              )}
            </div>
          )}

          {/* File Actions */}
          {selectedFile && !importBatch && (
            <div className="flex justify-center space-x-3">
              <Button
                onClick={validateFile}
                isLoading={isValidating}
                variant="secondary"
                disabled={!selectedFile}
              >
                <EyeIcon className="h-4 w-4 mr-2" />
                Validate & Preview
              </Button>
              
              {previewData?.is_valid && (
                <Button
                  onClick={executeImport}
                  isLoading={isUploading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Import {previewData.valid_rows} Users
                </Button>
              )}
            </div>
          )}

          {/* Preview Data */}
          {previewData && (
            <div className="space-y-4">
              {/* Validation Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">{previewData.total_rows}</div>
                  <div className="text-sm text-blue-700">Total Rows</div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">{previewData.valid_rows}</div>
                  <div className="text-sm text-green-700">Valid Users</div>
                </div>
                <div className="bg-red-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-600">{previewData.error_count}</div>
                  <div className="text-sm text-red-700">Errors</div>
                </div>
                <div className="bg-yellow-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-yellow-600">{previewData.duplicate_count}</div>
                  <div className="text-sm text-yellow-700">Duplicates</div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center space-x-3">
                {previewData.preview_data.length > 0 && (
                  <Button
                    onClick={() => setShowPreview(!showPreview)}
                    variant="secondary"
                  >
                    {showPreview ? 'Hide' : 'Show'} Preview
                  </Button>
                )}
                {(previewData.errors.length > 0 || previewData.duplicates.length > 0) && (
                  <Button
                    onClick={() => setShowErrors(!showErrors)}
                    variant="secondary"
                  >
                    {showErrors ? 'Hide' : 'Show'} Issues
                  </Button>
                )}
              </div>

              {/* Preview Table */}
              {showPreview && previewData.preview_data.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b">
                    <h4 className="font-medium text-gray-900">Preview (First 10 users)</h4>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Applications</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {previewData.preview_data.map((user, index) => (
                          <tr key={index}>
                            <td className="px-4 py-2 text-sm text-gray-900">{user.email}</td>
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {user.first_name} {user.last_name}
                            </td>
                            <td className="px-4 py-2 text-sm">
                              <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                {user.role}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-500">{user.department || '-'}</td>
                            <td className="px-4 py-2 text-sm">
                              <div className="flex space-x-1">
                                {user.applications.market_edge && (
                                  <span className="inline-flex px-1 py-0.5 text-xs bg-green-100 text-green-800 rounded">ME</span>
                                )}
                                {user.applications.causal_edge && (
                                  <span className="inline-flex px-1 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">CE</span>
                                )}
                                {user.applications.value_edge && (
                                  <span className="inline-flex px-1 py-0.5 text-xs bg-purple-100 text-purple-800 rounded">VE</span>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Errors and Duplicates */}
              {showErrors && (previewData.errors.length > 0 || previewData.duplicates.length > 0) && (
                <div className="space-y-4">
                  {previewData.errors.length > 0 && (
                    <div className="border border-red-200 rounded-lg">
                      <div className="bg-red-50 px-4 py-2 border-b border-red-200">
                        <h4 className="font-medium text-red-900">Validation Errors ({previewData.errors.length})</h4>
                      </div>
                      <div className="max-h-40 overflow-y-auto">
                        {previewData.errors.map((error, index) => (
                          <div key={index} className="px-4 py-2 border-b border-red-100 last:border-b-0">
                            <div className="text-sm">
                              <span className="font-medium text-red-900">Row {error.row}:</span>
                              <span className="text-red-700 ml-2">{sanitizeHTML(error.message)}</span>
                              {error.field && (
                                <span className="text-red-600 ml-2">({sanitizeHTML(error.field)})</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {previewData.duplicates.length > 0 && (
                    <div className="border border-yellow-200 rounded-lg">
                      <div className="bg-yellow-50 px-4 py-2 border-b border-yellow-200">
                        <h4 className="font-medium text-yellow-900">Duplicate Emails ({previewData.duplicates.length})</h4>
                      </div>
                      <div className="max-h-40 overflow-y-auto">
                        {previewData.duplicates.map((duplicate, index) => (
                          <div key={index} className="px-4 py-2 border-b border-yellow-100 last:border-b-0">
                            <div className="text-sm">
                              <span className="font-medium text-yellow-900">Row {duplicate.row}:</span>
                              <span className="text-yellow-700 ml-2">{sanitizeHTML(duplicate.email)}</span>
                              <span className="text-yellow-600 ml-2">- {sanitizeHTML(duplicate.message)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Import Progress */}
          {importBatch && (
            <div className="space-y-4">
              <div className="bg-white border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(importBatch.status)}
                    <h4 className="font-medium text-gray-900">Import Progress</h4>
                  </div>
                  <span className="text-sm text-gray-500 capitalize">{importBatch.status}</span>
                </div>
                
                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{getProgressPercentage()}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${getProgressPercentage()}%` }}
                    />
                  </div>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-lg font-semibold text-gray-900">{importBatch.total_rows}</div>
                    <div className="text-sm text-gray-500">Total</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-green-600">{importBatch.successful_rows}</div>
                    <div className="text-sm text-gray-500">Success</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-red-600">{importBatch.failed_rows}</div>
                    <div className="text-sm text-gray-500">Failed</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-blue-600">{importBatch.processed_rows}</div>
                    <div className="text-sm text-gray-500">Processed</div>
                  </div>
                </div>

                {importBatch.error_message && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-700">{importBatch.error_message}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            {importBatch?.status === 'completed' || importBatch?.status === 'failed' ? (
              <Button
                onClick={resetForm}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                Import Another File
              </Button>
            ) : null}
            <Button
              onClick={handleClose}
              variant="secondary"
            >
              {importBatch ? 'Close' : 'Cancel'}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}