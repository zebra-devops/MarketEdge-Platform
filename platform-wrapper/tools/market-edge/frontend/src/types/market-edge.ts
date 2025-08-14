export interface Market {
  id: string;
  name: string;
  geographic_bounds?: Record<string, any>;
  organisation_id: string;
  created_by: string;
  competitor_count: number;
  is_active: boolean;
  tracking_config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Competitor {
  id: string;
  name: string;
  market_id: string;
  organisation_id: string;
  business_type?: string;
  website?: string;
  locations?: Record<string, any>;
  tracking_priority: number;
  description?: string;
  market_share_estimate?: number;
  last_updated?: string;
  created_at: string;
}

export interface PricingData {
  id: string;
  competitor_id: string;
  market_id: string;
  product_service: string;
  price_point: number;
  currency: string;
  date_collected: string;
  source?: string;
  metadata?: Record<string, any>;
  is_promotion: boolean;
  promotion_details?: string;
  created_at: string;
}

export interface MarketAlert {
  id: string;
  market_id: string;
  organisation_id: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  trigger_data?: Record<string, any>;
  is_read: boolean;
  resolved_at?: string;
  created_at: string;
}

export interface MarketMetrics {
  period_start: string;
  period_end: string;
  total_data_points: number;
  average_price: number;
  median_price: number;
  min_price: number;
  max_price: number;
  price_range: number;
  standard_deviation: number;
  price_quartiles?: {
    q1: number;
    q2: number;
    q3: number;
  };
  competitors: Record<string, CompetitorMetrics>;
  trends: PricingTrends;
  anomalies: PriceAnomaly[];
}

export interface CompetitorMetrics {
  name: string;
  average_price: number;
  median_price: number;
  min_price: number;
  max_price: number;
  price_points_count: number;
  standard_deviation: number;
  price_rank: number;
  position: 'low' | 'mid' | 'high';
}

export interface PricingTrends {
  trend: 'increasing' | 'decreasing' | 'stable' | 'insufficient_data';
  weekly_averages: Record<string, number>;
  price_change: number;
  price_change_percent: number;
}

export interface PriceAnomaly {
  id: string;
  competitor_name: string;
  product_service: string;
  price: number;
  z_score: number;
  date_collected: string;
  deviation_from_mean: number;
  severity: 'medium' | 'high';
}

export interface MarketOverview {
  market: Market;
  competitors: Competitor[];
  metrics: MarketMetrics;
  recent_data_points: number;
  recent_alerts: MarketAlert[];
}

export interface CompetitorAnalysis {
  competitor: Competitor;
  pricing_metrics: {
    average_price: number;
    min_price: number;
    max_price: number;
    total_data_points: number;
    position_vs_market: 'below_market' | 'at_market' | 'above_market';
    market_average: number;
  };
  product_breakdown: Record<string, {
    average_price: number;
    min_price: number;
    max_price: number;
    data_points: number;
  }>;
  recent_pricing: PricingData[];
}

export interface CompetitorComparison {
  market_id: string;
  product_service_filter?: string;
  comparison_period: {
    start_date: string;
    end_date: string;
  };
  competitors: Record<string, {
    name: string;
    business_type?: string;
    average_price: number;
    min_price: number;
    max_price: number;
    data_points: number;
    products_services: string[];
    market_share_estimate?: number;
    tracking_priority: number;
    price_rank: number;
  }>;
  rankings: {
    by_price: Array<{
      competitor_id: string;
      name: string;
      average_price: number;
      rank: number;
    }>;
  };
}

export interface MarketTrends {
  period: {
    start_date: string;
    end_date: string;
    days_back: number;
  };
  filters: {
    competitor_id?: string;
    product_service?: string;
  };
  market_trend: Record<string, number>;
  competitor_trends: Record<string, {
    name: string;
    weekly_averages: Record<string, number>;
  }>;
  data_points_count: number;
}

export interface CompetitorMove {
  type: 'price_change' | 'new_products';
  competitor_id: string;
  competitor_name: string;
  change_type?: 'increase' | 'decrease';
  change_percent?: number;
  current_average?: number;
  previous_average?: number;
  new_products?: string[];
  significance: 'low' | 'medium' | 'high';
  detected_at: string;
}

export interface MarketReport {
  report_type: string;
  generated_at: string;
  market_overview: MarketOverview;
  competitor_analysis: CompetitorComparison;
  pricing_trends: MarketTrends;
  recent_moves: CompetitorMove[];
  insights: any[];
  summary: {
    total_competitors: number;
    active_alerts: number;
    recent_moves: number;
    key_insights: number;
  };
}