import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/components/providers/AuthProvider'
import { QueryProvider } from '@/components/providers/QueryProvider'
import { ToastProvider } from '@/components/providers/ToastProvider'
import { OrganisationProvider } from '@/components/providers/OrganisationProvider'
import { FeatureFlagProvider } from '@/components/providers/FeatureFlagProvider'
import AuthDebugPanel from '@/components/dev/AuthDebugPanel'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Platform Wrapper - Business Intelligence Suite',
  description: 'Multi-tenant platform for business intelligence tools',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <QueryProvider>
          <AuthProvider>
            <OrganisationProvider>
              <FeatureFlagProvider
                preloadFlags={['market_edge.enhanced_ui', 'admin.advanced_controls']}
                enableRealTimeUpdates={true}
                debugMode={process.env.NODE_ENV === 'development'}
              >
                <ToastProvider>
                  {children}
                  <AuthDebugPanel />
                </ToastProvider>
              </FeatureFlagProvider>
            </OrganisationProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  )
}