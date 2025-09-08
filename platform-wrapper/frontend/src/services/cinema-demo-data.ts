import { 
  Market, 
  Competitor, 
  PricingData, 
  MarketAlert, 
  MarketOverview,
  MarketMetrics,
  CompetitorComparison,
  MarketTrends,
  CompetitorAnalysis 
} from '@/types/market-edge';

// Cinema-specific demo data for Odeon presentation
export class CinemaDemoDataService {
  // UK Cinema Market Data
  private readonly ukCinemaMarket: Market = {
    id: 'uk-cinema-market-2024',
    name: 'UK Cinema Exhibition Market',
    geographic_bounds: {
      country: 'United Kingdom',
      regions: ['England', 'Scotland', 'Wales', 'Northern Ireland'],
      focus_areas: ['London', 'Birmingham', 'Manchester', 'Glasgow', 'Leeds']
    },
    organisation_id: 'odeon-demo-org',
    created_by: 'odeon-market-analyst',
    competitor_count: 4,
    is_active: true,
    tracking_config: {
      industry_type: 'cinema_exhibition',
      sic_code: '59140',
      metrics: ['ticket_prices', 'concession_prices', 'membership_fees', 'premium_experiences'],
      update_frequency: 'daily',
      alert_thresholds: {
        price_change: 0.05, // 5% change triggers alert
        new_competitor: true,
        market_share_shift: 0.02 // 2% market share change
      }
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-08-14T10:00:00Z'
  };

  // Major UK Cinema Competitors
  private readonly competitors: Competitor[] = [
    {
      id: 'vue-cinemas-uk',
      name: 'Vue Entertainment',
      market_id: 'uk-cinema-market-2024',
      organisation_id: 'odeon-demo-org',
      business_type: 'Cinema Chain',
      website: 'https://www.myvue.com',
      locations: {
        total_sites: 91,
        total_screens: 840,
        regions: {
          'London': 15,
          'South East': 18,
          'Midlands': 12,
          'North': 20,
          'Scotland': 8,
          'Wales': 6,
          'N. Ireland': 3
        }
      },
      tracking_priority: 10, // Highest priority - main competitor
      description: 'Leading UK cinema chain with premium and IMAX offerings',
      market_share_estimate: 0.21, // 21% market share
      last_updated: '2024-08-14T08:00:00Z',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 'cineworld-uk',
      name: 'Cineworld Group',
      market_id: 'uk-cinema-market-2024',
      organisation_id: 'odeon-demo-org',
      business_type: 'Cinema Chain',
      website: 'https://www.cineworld.co.uk',
      locations: {
        total_sites: 99,
        total_screens: 1015,
        regions: {
          'London': 8,
          'South East': 22,
          'Midlands': 15,
          'North': 25,
          'Scotland': 12,
          'Wales': 9,
          'N. Ireland': 4
        }
      },
      tracking_priority: 10, // Highest priority
      description: 'Global cinema chain with strong UK presence, 4DX and IMAX',
      market_share_estimate: 0.25, // 25% market share
      last_updated: '2024-08-14T08:00:00Z',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 'empire-cinemas',
      name: 'Empire Cinemas',
      market_id: 'uk-cinema-market-2024',
      organisation_id: 'odeon-demo-org',
      business_type: 'Cinema Chain',
      website: 'https://empirecinemas.co.uk',
      locations: {
        total_sites: 14,
        total_screens: 130,
        regions: {
          'London': 4,
          'South East': 6,
          'Midlands': 2,
          'North': 2,
          'Scotland': 0,
          'Wales': 0,
          'N. Ireland': 0
        }
      },
      tracking_priority: 7, // Medium priority
      description: 'Premium cinema experience with luxury seating and IMAX',
      market_share_estimate: 0.03, // 3% market share
      last_updated: '2024-08-14T08:00:00Z',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 'showcase-cinemas',
      name: 'Showcase Cinemas',
      market_id: 'uk-cinema-market-2024',
      organisation_id: 'odeon-demo-org',
      business_type: 'Cinema Chain',
      website: 'https://www.showcasecinemas.co.uk',
      locations: {
        total_sites: 21,
        total_screens: 285,
        regions: {
          'London': 3,
          'South East': 8,
          'Midlands': 4,
          'North': 6,
          'Scotland': 0,
          'Wales': 0,
          'N. Ireland': 0
        }
      },
      tracking_priority: 8, // Medium-high priority
      description: 'American-owned chain with XPlus premium format',
      market_share_estimate: 0.07, // 7% market share
      last_updated: '2024-08-14T08:00:00Z',
      created_at: '2024-01-01T00:00:00Z'
    }
  ];

  // Current pricing data for cinema services
  private readonly pricingData: PricingData[] = [
    // Vue Cinema Pricing
    { 
      id: 'vue-adult-std-2024080', 
      competitor_id: 'vue-cinemas-uk', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Standard Ticket', 
      price_point: 12.99, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'vue_website_scraper',
      metadata: { location: 'London West End', time_slot: 'peak' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },
    { 
      id: 'vue-adult-prem-2024080', 
      competitor_id: 'vue-cinemas-uk', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Premium Seat', 
      price_point: 18.99, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'vue_website_scraper',
      metadata: { location: 'London West End', time_slot: 'peak', seat_type: 'premium_plus' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },
    { 
      id: 'vue-large-popcorn-2024080', 
      competitor_id: 'vue-cinemas-uk', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Large Popcorn', 
      price_point: 6.50, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'vue_website_scraper',
      metadata: { concession_type: 'sweet', size: 'large' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },
    
    // Cineworld Pricing
    { 
      id: 'cineworld-adult-std-2024080', 
      competitor_id: 'cineworld-uk', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Standard Ticket', 
      price_point: 11.70, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'cineworld_api',
      metadata: { location: 'London Leicester Square', time_slot: 'peak' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },
    { 
      id: 'cineworld-adult-prem-2024080', 
      competitor_id: 'cineworld-uk', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Premium Seat', 
      price_point: 21.40, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'cineworld_api',
      metadata: { location: 'London Leicester Square', time_slot: 'peak', seat_type: '4dx' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },
    { 
      id: 'cineworld-unlimited-2024080', 
      competitor_id: 'cineworld-uk', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Monthly Unlimited Pass', 
      price_point: 17.90, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'cineworld_api',
      metadata: { subscription_type: 'unlimited', billing: 'monthly' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },

    // Empire Cinemas Pricing
    { 
      id: 'empire-adult-std-2024080', 
      competitor_id: 'empire-cinemas', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Standard Ticket', 
      price_point: 15.50, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'empire_manual_check',
      metadata: { location: 'London Leicester Square IMAX', time_slot: 'peak' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },
    { 
      id: 'empire-adult-prem-2024080', 
      competitor_id: 'empire-cinemas', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Premium Seat', 
      price_point: 22.50, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'empire_manual_check',
      metadata: { location: 'London Leicester Square IMAX', time_slot: 'peak', seat_type: 'imax_premium' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },

    // Showcase Cinemas Pricing
    { 
      id: 'showcase-adult-std-2024080', 
      competitor_id: 'showcase-cinemas', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Standard Ticket', 
      price_point: 10.99, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'showcase_scraper',
      metadata: { location: 'Reading', time_slot: 'peak' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    },
    { 
      id: 'showcase-adult-xplus-2024080', 
      competitor_id: 'showcase-cinemas', 
      market_id: 'uk-cinema-market-2024',
      product_service: 'Adult Premium Seat', 
      price_point: 16.99, 
      currency: 'GBP',
      date_collected: '2024-08-14T10:00:00Z',
      source: 'showcase_scraper',
      metadata: { location: 'Reading', time_slot: 'peak', seat_type: 'xplus' },
      is_promotion: false,
      created_at: '2024-08-14T10:00:00Z'
    }
  ];

  // Market alerts focused on cinema industry insights
  private readonly marketAlerts: MarketAlert[] = [
    {
      id: 'alert-cineworld-pricing-2024080',
      market_id: 'uk-cinema-market-2024',
      organisation_id: 'odeon-demo-org',
      alert_type: 'pricing_intelligence',
      severity: 'high',
      title: 'Cineworld Reduces Premium Pricing',
      message: 'Cineworld has reduced 4DX ticket prices by 8% across London venues, potentially impacting premium market positioning.',
      trigger_data: {
        competitor: 'Cineworld Group',
        price_change: -0.08,
        affected_product: 'Adult Premium Seat',
        locations_affected: ['London Leicester Square', 'London O2', 'London Wood Green']
      },
      is_read: false,
      created_at: '2024-08-14T09:30:00Z'
    },
    {
      id: 'alert-vue-expansion-2024080',
      market_id: 'uk-cinema-market-2024',
      organisation_id: 'odeon-demo-org',
      alert_type: 'competitive_moves',
      severity: 'medium',
      title: 'Vue Announces New IMAX Locations',
      message: 'Vue Entertainment planning 3 new IMAX installations in Manchester, Birmingham, and Glasgow for Q4 2024.',
      trigger_data: {
        competitor: 'Vue Entertainment',
        expansion_type: 'premium_screens',
        locations: ['Manchester', 'Birmingham', 'Glasgow'],
        planned_opening: 'Q4 2024'
      },
      is_read: false,
      created_at: '2024-08-13T14:20:00Z'
    },
    {
      id: 'alert-showcase-membership-2024080',
      market_id: 'uk-cinema-market-2024',
      organisation_id: 'odeon-demo-org',
      alert_type: 'product_intelligence',
      severity: 'medium',
      title: 'Showcase Launches Subscription Service',
      message: 'Showcase Cinemas introduces unlimited monthly pass at £14.99, undercutting Cineworld Unlimited by £2.91.',
      trigger_data: {
        competitor: 'Showcase Cinemas',
        new_product: 'Unlimited Monthly Pass',
        price_point: 14.99,
        competitive_advantage: 'Price leadership in subscriptions'
      },
      is_read: true,
      created_at: '2024-08-12T11:45:00Z'
    }
  ];

  // Get market data for demo
  getMarket(): Market {
    return this.ukCinemaMarket;
  }

  getCompetitors(): Competitor[] {
    return this.competitors;
  }

  getPricingData(): PricingData[] {
    return this.pricingData;
  }

  getMarketAlerts(): MarketAlert[] {
    return this.marketAlerts;
  }

  // Generate comprehensive market overview for demo
  getMarketOverview(): MarketOverview {
    const metrics: MarketMetrics = {
      period_start: '2024-07-15T00:00:00Z',
      period_end: '2024-08-14T23:59:59Z',
      total_data_points: this.pricingData.length,
      average_price: 15.23,
      median_price: 15.50,
      min_price: 6.50,
      max_price: 22.50,
      price_range: 16.00,
      standard_deviation: 4.85,
      price_quartiles: {
        q1: 11.35,
        q2: 15.50,
        q3: 18.99
      },
      competitors: {
        'vue-cinemas-uk': {
          name: 'Vue Entertainment',
          average_price: 12.83,
          median_price: 12.99,
          min_price: 6.50,
          max_price: 18.99,
          price_points_count: 3,
          standard_deviation: 6.24,
          price_rank: 2,
          position: 'mid'
        },
        'cineworld-uk': {
          name: 'Cineworld Group',
          average_price: 16.33,
          median_price: 17.90,
          min_price: 11.70,
          max_price: 21.40,
          price_points_count: 3,
          standard_deviation: 4.91,
          price_rank: 3,
          position: 'mid'
        },
        'empire-cinemas': {
          name: 'Empire Cinemas',
          average_price: 19.00,
          median_price: 19.00,
          min_price: 15.50,
          max_price: 22.50,
          price_points_count: 2,
          standard_deviation: 3.50,
          price_rank: 4,
          position: 'high'
        },
        'showcase-cinemas': {
          name: 'Showcase Cinemas',
          average_price: 13.99,
          median_price: 13.99,
          min_price: 10.99,
          max_price: 16.99,
          price_points_count: 2,
          standard_deviation: 3.00,
          price_rank: 1,
          position: 'low'
        }
      },
      trends: {
        trend: 'stable',
        weekly_averages: {
          '2024-08-05': 15.45,
          '2024-08-06': 15.23,
          '2024-08-07': 15.18,
          '2024-08-08': 15.31,
          '2024-08-09': 15.20,
          '2024-08-10': 15.15,
          '2024-08-11': 15.23
        },
        price_change: -0.22,
        price_change_percent: -1.4
      },
      anomalies: [
        {
          id: 'anomaly-empire-premium-2024080',
          competitor_name: 'Empire Cinemas',
          product_service: 'Adult Premium Seat',
          price: 22.50,
          z_score: 2.3,
          date_collected: '2024-08-14T10:00:00Z',
          deviation_from_mean: 7.27,
          severity: 'medium'
        }
      ]
    };

    return {
      market: this.ukCinemaMarket,
      competitors: this.competitors,
      metrics,
      recent_data_points: this.pricingData.length,
      recent_alerts: this.marketAlerts
    };
  }

  // Generate competitor comparison data
  getCompetitorComparison(): CompetitorComparison {
    return {
      market_id: 'uk-cinema-market-2024',
      comparison_period: {
        start_date: '2024-07-15T00:00:00Z',
        end_date: '2024-08-14T23:59:59Z'
      },
      competitors: {
        'vue-cinemas-uk': {
          name: 'Vue Entertainment',
          business_type: 'Cinema Chain',
          average_price: 12.83,
          min_price: 6.50,
          max_price: 18.99,
          data_points: 3,
          products_services: ['Adult Standard Ticket', 'Adult Premium Seat', 'Large Popcorn'],
          market_share_estimate: 0.21,
          tracking_priority: 10,
          price_rank: 2
        },
        'cineworld-uk': {
          name: 'Cineworld Group',
          business_type: 'Cinema Chain',
          average_price: 16.33,
          min_price: 11.70,
          max_price: 21.40,
          data_points: 3,
          products_services: ['Adult Standard Ticket', 'Adult Premium Seat', 'Monthly Unlimited Pass'],
          market_share_estimate: 0.25,
          tracking_priority: 10,
          price_rank: 3
        },
        'empire-cinemas': {
          name: 'Empire Cinemas',
          business_type: 'Cinema Chain',
          average_price: 19.00,
          min_price: 15.50,
          max_price: 22.50,
          data_points: 2,
          products_services: ['Adult Standard Ticket', 'Adult Premium Seat'],
          market_share_estimate: 0.03,
          tracking_priority: 7,
          price_rank: 4
        },
        'showcase-cinemas': {
          name: 'Showcase Cinemas',
          business_type: 'Cinema Chain',
          average_price: 13.99,
          min_price: 10.99,
          max_price: 16.99,
          data_points: 2,
          products_services: ['Adult Standard Ticket', 'Adult Premium Seat'],
          market_share_estimate: 0.07,
          tracking_priority: 8,
          price_rank: 1
        }
      },
      rankings: {
        by_price: [
          { competitor_id: 'showcase-cinemas', name: 'Showcase Cinemas', average_price: 13.99, rank: 1 },
          { competitor_id: 'vue-cinemas-uk', name: 'Vue Entertainment', average_price: 12.83, rank: 2 },
          { competitor_id: 'cineworld-uk', name: 'Cineworld Group', average_price: 16.33, rank: 3 },
          { competitor_id: 'empire-cinemas', name: 'Empire Cinemas', average_price: 19.00, rank: 4 }
        ]
      }
    };
  }

  // Generate market trends data
  getMarketTrends(): MarketTrends {
    return {
      period: {
        start_date: '2024-07-15T00:00:00Z',
        end_date: '2024-08-14T23:59:59Z',
        days_back: 30
      },
      filters: {},
      market_trend: {
        '2024-07-15': 15.67,
        '2024-07-22': 15.58,
        '2024-07-29': 15.49,
        '2024-08-05': 15.45,
        '2024-08-12': 15.23
      },
      competitor_trends: {
        'vue-cinemas-uk': {
          name: 'Vue Entertainment',
          weekly_averages: {
            '2024-07-15': 12.95,
            '2024-07-22': 12.91,
            '2024-07-29': 12.88,
            '2024-08-05': 12.86,
            '2024-08-12': 12.83
          }
        },
        'cineworld-uk': {
          name: 'Cineworld Group',
          weekly_averages: {
            '2024-07-15': 16.85,
            '2024-07-22': 16.79,
            '2024-07-29': 16.67,
            '2024-08-05': 16.45,
            '2024-08-12': 16.33
          }
        },
        'empire-cinemas': {
          name: 'Empire Cinemas',
          weekly_averages: {
            '2024-07-15': 19.25,
            '2024-07-22': 19.15,
            '2024-07-29': 19.08,
            '2024-08-05': 19.02,
            '2024-08-12': 19.00
          }
        },
        'showcase-cinemas': {
          name: 'Showcase Cinemas',
          weekly_averages: {
            '2024-07-15': 14.25,
            '2024-07-22': 14.15,
            '2024-07-29': 14.08,
            '2024-08-05': 14.02,
            '2024-08-12': 13.99
          }
        }
      },
      data_points_count: this.pricingData.length
    };
  }

  // Get all markets (for demo, just return the UK cinema market)
  getMarkets(): Market[] {
    return [this.ukCinemaMarket];
  }

  // Get competitor analysis for individual competitor
  getCompetitorAnalysis(competitorId: string): CompetitorAnalysis | null {
    const competitor = this.competitors.find(c => c.id === competitorId);
    if (!competitor) return null;

    const competitorPricing = this.pricingData.filter(p => p.competitor_id === competitorId);
    const prices = competitorPricing.map(p => p.price_point);
    
    return {
      competitor,
      pricing_metrics: {
        average_price: prices.reduce((a, b) => a + b, 0) / prices.length || 0,
        min_price: Math.min(...prices) || 0,
        max_price: Math.max(...prices) || 0,
        total_data_points: prices.length,
        position_vs_market: 'at_market', // This would be calculated
        market_average: 15.23
      },
      product_breakdown: competitorPricing.reduce((acc, pricing) => {
        if (!acc[pricing.product_service]) {
          acc[pricing.product_service] = {
            average_price: pricing.price_point,
            min_price: pricing.price_point,
            max_price: pricing.price_point,
            data_points: 1
          };
        }
        return acc;
      }, {} as Record<string, any>),
      recent_pricing: competitorPricing
    };
  }
}

export const cinemaDemoData = new CinemaDemoDataService();