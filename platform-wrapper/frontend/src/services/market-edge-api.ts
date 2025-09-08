import { 
  Market, 
  Competitor, 
  PricingData, 
  MarketAlert, 
  MarketOverview,
  MarketMetrics,
  CompetitorAnalysis,
  CompetitorComparison,
  MarketTrends,
  MarketReport
} from '@/types/market-edge';
import { cinemaDemoData } from './cinema-demo-data';
import Cookies from 'js-cookie';

const API_BASE = 'http://localhost:8000/api/v1/market-edge';

class MarketEdgeAPI {
  private isDemoMode: boolean = false;

  // Enable/disable demo mode for cinema presentation
  setDemoMode(enabled: boolean) {
    this.isDemoMode = enabled;
    console.log(`Market Edge API Demo Mode: ${enabled ? 'ENABLED' : 'DISABLED'}`);
  }

  getDemoMode(): boolean {
    return this.isDemoMode;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const token = Cookies.get('access_token');
    
    // Debug logging
    console.log('Market Edge API Request:', {
      endpoint: `${API_BASE}${endpoint}`,
      hasToken: !!token,
      token: token ? `${token.substring(0, 20)}...` : 'No token'
    });
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Market endpoints
  async getMarkets(): Promise<Market[]> {
    if (this.isDemoMode) {
      // Return cinema demo markets with slight delay for realism
      await new Promise(resolve => setTimeout(resolve, 300));
      return cinemaDemoData.getMarkets();
    }
    return this.request<Market[]>('/markets');
  }

  async createMarket(marketData: {
    name: string;
    geographic_bounds?: Record<string, any>;
    tracking_config?: Record<string, any>;
  }): Promise<Market> {
    return this.request<Market>('/markets', {
      method: 'POST',
      body: JSON.stringify(marketData),
    });
  }

  async getMarket(marketId: string): Promise<Market> {
    return this.request<Market>(`/markets/${marketId}`);
  }

  async updateMarket(
    marketId: string, 
    marketData: {
      name: string;
      geographic_bounds?: Record<string, any>;
      tracking_config?: Record<string, any>;
    }
  ): Promise<Market> {
    return this.request<Market>(`/markets/${marketId}`, {
      method: 'PUT',
      body: JSON.stringify(marketData),
    });
  }

  async deleteMarket(marketId: string): Promise<void> {
    await this.request(`/markets/${marketId}`, {
      method: 'DELETE',
    });
  }

  // Competitor endpoints
  async getCompetitors(marketId: string): Promise<Competitor[]> {
    return this.request<Competitor[]>(`/markets/${marketId}/competitors`);
  }

  async createCompetitor(competitorData: {
    name: string;
    market_id: string;
    business_type?: string;
    website?: string;
    locations?: Record<string, any>;
    tracking_priority?: number;
    description?: string;
    market_share_estimate?: number;
  }): Promise<Competitor> {
    return this.request<Competitor>('/competitors', {
      method: 'POST',
      body: JSON.stringify(competitorData),
    });
  }

  async getCompetitor(competitorId: string): Promise<Competitor> {
    return this.request<Competitor>(`/competitors/${competitorId}`);
  }

  async updateCompetitor(
    competitorId: string,
    competitorData: {
      name: string;
      market_id: string;
      business_type?: string;
      website?: string;
      locations?: Record<string, any>;
      tracking_priority?: number;
      description?: string;
      market_share_estimate?: number;
    }
  ): Promise<Competitor> {
    return this.request<Competitor>(`/competitors/${competitorId}`, {
      method: 'PUT',
      body: JSON.stringify(competitorData),
    });
  }

  // Pricing data endpoints
  async createPricingData(pricingData: {
    competitor_id: string;
    product_service: string;
    price_point: number;
    currency?: string;
    date_collected: string;
    source?: string;
    metadata?: Record<string, any>;
    is_promotion?: boolean;
    promotion_details?: string;
  }): Promise<PricingData> {
    return this.request<PricingData>('/pricing-data', {
      method: 'POST',
      body: JSON.stringify(pricingData),
    });
  }

  async getMarketPricingData(
    marketId: string,
    options: {
      competitor_id?: string;
      product_service?: string;
      limit?: number;
    } = {}
  ): Promise<PricingData[]> {
    const params = new URLSearchParams();
    if (options.competitor_id) params.append('competitor_id', options.competitor_id);
    if (options.product_service) params.append('product_service', options.product_service);
    if (options.limit) params.append('limit', options.limit.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<PricingData[]>(`/markets/${marketId}/pricing-data${query}`);
  }

  // Analysis endpoints
  async getMarketOverview(marketId: string): Promise<MarketOverview> {
    if (this.isDemoMode) {
      // Return cinema demo market overview with delay for realism
      await new Promise(resolve => setTimeout(resolve, 500));
      return cinemaDemoData.getMarketOverview();
    }
    return this.request<MarketOverview>(`/markets/${marketId}/overview`);
  }

  async getMarketAnalysis(
    marketId: string,
    options: {
      product_service?: string;
      days_back?: number;
    } = {}
  ): Promise<MarketMetrics> {
    const params = new URLSearchParams();
    if (options.product_service) params.append('product_service', options.product_service);
    if (options.days_back) params.append('days_back', options.days_back.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<MarketMetrics>(`/markets/${marketId}/analysis${query}`);
  }

  async getCompetitorAnalysis(
    competitorId: string,
    options: {
      days_back?: number;
    } = {}
  ): Promise<CompetitorAnalysis> {
    const params = new URLSearchParams();
    if (options.days_back) params.append('days_back', options.days_back.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<CompetitorAnalysis>(`/competitors/${competitorId}/analysis${query}`);
  }

  async compareCompetitors(
    marketId: string,
    options: {
      competitor_ids?: string[];
      product_service?: string;
    } = {}
  ): Promise<CompetitorComparison> {
    if (this.isDemoMode) {
      // Return cinema competitor comparison with delay for realism
      await new Promise(resolve => setTimeout(resolve, 400));
      return cinemaDemoData.getCompetitorComparison();
    }
    
    const params = new URLSearchParams();
    if (options.competitor_ids) {
      params.append('competitor_ids', options.competitor_ids.join(','));
    }
    if (options.product_service) params.append('product_service', options.product_service);

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<CompetitorComparison>(`/markets/${marketId}/comparison${query}`);
  }

  async getPricingTrends(
    marketId: string,
    options: {
      competitor_id?: string;
      product_service?: string;
      days_back?: number;
    } = {}
  ): Promise<MarketTrends> {
    if (this.isDemoMode) {
      // Return cinema pricing trends with delay for realism
      await new Promise(resolve => setTimeout(resolve, 450));
      return cinemaDemoData.getMarketTrends();
    }
    
    const params = new URLSearchParams();
    if (options.competitor_id) params.append('competitor_id', options.competitor_id);
    if (options.product_service) params.append('product_service', options.product_service);
    if (options.days_back) params.append('days_back', options.days_back.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<MarketTrends>(`/markets/${marketId}/trends${query}`);
  }

  // Alert endpoints
  async getMarketAlerts(
    marketId: string,
    options: {
      unread_only?: boolean;
      limit?: number;
    } = {}
  ): Promise<MarketAlert[]> {
    const params = new URLSearchParams();
    if (options.unread_only) params.append('unread_only', 'true');
    if (options.limit) params.append('limit', options.limit.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<MarketAlert[]>(`/markets/${marketId}/alerts${query}`);
  }

  async markAlertRead(alertId: string): Promise<void> {
    await this.request(`/alerts/${alertId}/mark-read`, {
      method: 'POST',
    });
  }

  // Report endpoints
  async generateMarketReport(
    marketId: string,
    reportType: 'comprehensive' | 'summary' | 'trends' = 'comprehensive'
  ): Promise<MarketReport> {
    const params = new URLSearchParams();
    params.append('report_type', reportType);

    return this.request<MarketReport>(`/markets/${marketId}/report?${params.toString()}`);
  }

  // Utility methods
  async searchMarkets(query: string): Promise<Market[]> {
    const markets = await this.getMarkets();
    return markets.filter(market => 
      market.name.toLowerCase().includes(query.toLowerCase())
    );
  }

  async getMarketSummary(marketId: string) {
    const [overview, alerts] = await Promise.all([
      this.getMarketOverview(marketId),
      this.getMarketAlerts(marketId, { unread_only: true, limit: 5 })
    ]);

    return {
      ...overview,
      unread_alerts: alerts
    };
  }

  // Export functionality
  async exportMarketData(
    marketId: string,
    format: 'csv' | 'pdf' = 'csv',
    options: {
      include_pricing?: boolean;
      include_competitors?: boolean;
      include_trends?: boolean;
      date_range?: {
        start: string;
        end: string;
      };
    } = {}
  ): Promise<Blob> {
    // This would typically call a dedicated export endpoint
    // For now, we'll generate the data client-side
    const overview = await this.getMarketOverview(marketId);
    
    if (format === 'csv') {
      return this.generateCSVExport(overview, options);
    } else {
      return this.generatePDFExport(overview, options);
    }
  }

  private async generateCSVExport(
    overview: MarketOverview, 
    options: any
  ): Promise<Blob> {
    let csvContent = 'Market Edge Export\n\n';
    
    // Market info
    csvContent += `Market,${overview.market.name}\n`;
    csvContent += `Competitors,${overview.competitors.length}\n`;
    csvContent += `Data Points,${overview.recent_data_points}\n\n`;
    
    // Competitors
    if (options.include_competitors !== false) {
      csvContent += 'Competitor Name,Business Type,Market Share,Tracking Priority\n';
      overview.competitors.forEach(comp => {
        csvContent += `${comp.name},${comp.business_type || ''},${comp.market_share_estimate || ''},${comp.tracking_priority}\n`;
      });
    }
    
    return new Blob([csvContent], { type: 'text/csv' });
  }

  private async generatePDFExport(
    overview: MarketOverview, 
    options: any
  ): Promise<Blob> {
    // This would use a PDF library like jsPDF
    // For now, return a simple text blob
    const content = `Market Edge Report - ${overview.market.name}`;
    return new Blob([content], { type: 'application/pdf' });
  }
}

export const marketEdgeAPI = new MarketEdgeAPI();