#!/usr/bin/env python3
"""
Performance benchmark validation script for MarketEdge platform
"""
import time
import statistics
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())
os.environ['PYTHONPATH'] = os.getcwd()

def run_performance_benchmarks():
    print('Running performance benchmarks...')
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Performance test endpoints
        endpoints_to_test = [
            '/',
            '/health',
            '/deployment-test',
            '/system/status'
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            print(f'\nBenchmarking {endpoint}...')
            response_times = []
            
            # Warm up
            for _ in range(3):
                client.get(endpoint)
            
            # Actual benchmark
            for i in range(10):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                response_times.append(response_time)
                
                if response.status_code != 200:
                    print(f'  Warning: Status code {response.status_code} on attempt {i+1}')
            
            # Calculate statistics
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            results[endpoint] = {
                'avg_ms': round(avg_time, 2),
                'median_ms': round(median_time, 2),
                'min_ms': round(min_time, 2),
                'max_ms': round(max_time, 2)
            }
            
            print(f'  Average: {avg_time:.2f}ms')
            print(f'  Median: {median_time:.2f}ms')
            print(f'  Min: {min_time:.2f}ms')
            print(f'  Max: {max_time:.2f}ms')
        
        # Performance assessment
        print(f'\n=== PERFORMANCE ASSESSMENT ===')
        health_avg = results['/health']['avg_ms']
        if health_avg < 100:
            print(f'✅ Health endpoint performance: EXCELLENT ({health_avg:.2f}ms)')
        elif health_avg < 500:
            print(f'✅ Health endpoint performance: GOOD ({health_avg:.2f}ms)')
        else:
            print(f'⚠️  Health endpoint performance: NEEDS IMPROVEMENT ({health_avg:.2f}ms)')
        
        print('\n✅ Performance benchmarks completed!')
        return results
        
    except Exception as e:
        print(f'❌ Performance benchmark error: {e}')
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    run_performance_benchmarks()