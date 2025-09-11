import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
from models import ForecastingData
import logging

class ForecastingEngine:
    """Advanced forecasting engine for demand prediction"""
    
    def __init__(self):
        self.moving_average_window = 3
        self.exponential_smoothing_alpha = 0.3
    
    def moving_average_forecast(self, data, periods=1):
        """Simple moving average forecasting"""
        if len(data) < self.moving_average_window:
            return None, 0
        
        # Calculate moving average
        ma_values = []
        for i in range(self.moving_average_window - 1, len(data)):
            window_data = data[i - self.moving_average_window + 1:i + 1]
            ma_values.append(np.mean(window_data))
        
        # Forecast future periods
        forecasts = []
        last_ma = ma_values[-1]
        
        for _ in range(periods):
            forecasts.append(last_ma)
        
        # Calculate confidence (based on variance of recent data)
        recent_variance = np.var(data[-self.moving_average_window:])
        confidence = max(0, min(100, 100 - (recent_variance / np.mean(data[-self.moving_average_window:]) * 50)))
        
        return forecasts, confidence
    
    def exponential_smoothing_forecast(self, data, periods=1):
        """Exponential smoothing forecasting"""
        if len(data) < 2:
            return None, 0
        
        # Initialize
        smoothed = [data[0]]
        
        # Apply exponential smoothing
        for i in range(1, len(data)):
            smoothed_value = self.exponential_smoothing_alpha * data[i] + \
                           (1 - self.exponential_smoothing_alpha) * smoothed[i-1]
            smoothed.append(smoothed_value)
        
        # Forecast future periods
        forecasts = []
        last_smoothed = smoothed[-1]
        
        for _ in range(periods):
            forecasts.append(last_smoothed)
        
        # Calculate confidence based on recent trend stability
        recent_trend = np.mean(np.diff(data[-min(6, len(data)):]))
        trend_stability = 1 - abs(recent_trend) / (np.mean(data[-min(6, len(data)):]) + 1e-6)
        confidence = max(0, min(100, trend_stability * 100))
        
        return forecasts, confidence
    
    def trend_analysis_forecast(self, data, periods=1):
        """Linear trend analysis forecasting"""
        if len(data) < 3:
            return None, 0
        
        # Create time series
        x = np.arange(len(data))
        y = np.array(data)
        
        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs
        
        # Forecast future periods
        forecasts = []
        for i in range(1, periods + 1):
            future_x = len(data) + i - 1
            forecast_value = slope * future_x + intercept
            forecasts.append(max(0, forecast_value))  # Ensure non-negative
        
        # Calculate R-squared for confidence
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        confidence = max(0, min(100, r_squared * 100))
        
        return forecasts, confidence
    
    def seasonal_forecast(self, data, periods=1, season_length=12):
        """Seasonal forecasting using seasonal decomposition"""
        if len(data) < season_length * 2:
            return None, 0
        
        # Convert to pandas Series for seasonal decomposition
        df = pd.DataFrame({'value': data})
        df.index = pd.date_range(start='2020-01-01', periods=len(data), freq='M')
        
        try:
            # Simple seasonal average
            seasonal_pattern = []
            for month in range(season_length):
                month_data = [data[i] for i in range(month, len(data), season_length)]
                if month_data:
                    seasonal_pattern.append(np.mean(month_data))
            
            # Forecast using seasonal pattern
            forecasts = []
            for i in range(periods):
                seasonal_index = (len(data) + i) % season_length
                base_forecast = np.mean(data[-season_length:]) if len(data) >= season_length else np.mean(data)
                seasonal_factor = seasonal_pattern[seasonal_index] / np.mean(seasonal_pattern) if np.mean(seasonal_pattern) > 0 else 1
                forecasts.append(base_forecast * seasonal_factor)
            
            # Calculate confidence based on seasonal consistency
            seasonal_consistency = 1 - np.std(seasonal_pattern) / (np.mean(seasonal_pattern) + 1e-6)
            confidence = max(0, min(100, seasonal_consistency * 100))
            
            return forecasts, confidence
            
        except Exception as e:
            logging.error(f"Seasonal forecasting error: {str(e)}")
            return None, 0
    
    def ensemble_forecast(self, data, periods=1):
        """Ensemble forecasting combining multiple methods"""
        forecasts = {}
        confidences = {}
        
        # Get forecasts from different methods
        ma_forecast, ma_conf = self.moving_average_forecast(data, periods)
        if ma_forecast:
            forecasts['moving_average'] = ma_forecast
            confidences['moving_average'] = ma_conf
        
        es_forecast, es_conf = self.exponential_smoothing_forecast(data, periods)
        if es_forecast:
            forecasts['exponential_smoothing'] = es_forecast
            confidences['exponential_smoothing'] = es_conf
        
        trend_forecast, trend_conf = self.trend_analysis_forecast(data, periods)
        if trend_forecast:
            forecasts['trend_analysis'] = trend_forecast
            confidences['trend_analysis'] = trend_conf
        
        seasonal_forecast, seasonal_conf = self.seasonal_forecast(data, periods)
        if seasonal_forecast:
            forecasts['seasonal'] = seasonal_forecast
            confidences['seasonal'] = seasonal_conf
        
        if not forecasts:
            return None, 0
        
        # Weighted average based on confidence
        total_weight = sum(confidences.values())
        if total_weight == 0:
            return None, 0
        
        ensemble_forecast = []
        for i in range(periods):
            weighted_sum = 0
            for method, forecast in forecasts.items():
                weight = confidences[method] / total_weight
                weighted_sum += forecast[i] * weight
            ensemble_forecast.append(weighted_sum)
        
        # Average confidence
        avg_confidence = np.mean(list(confidences.values()))
        
        return ensemble_forecast, avg_confidence
    
    def generate_forecast(self, product_id, warehouse_id, periods=12, method='ensemble'):
        """Generate forecast for a specific product and warehouse"""
        try:
            # Get sales history
            sales_data = ForecastingData.get_sales_history(product_id, warehouse_id, months=24)
            
            if not sales_data:
                return None, "No sales history available"
            
            # Extract quantities
            quantities = [record['total_quantity'] for record in sales_data]
            
            if len(quantities) < 3:
                return None, "Insufficient data for forecasting"
            
            # Generate forecast based on method
            if method == 'moving_average':
                forecast, confidence = self.moving_average_forecast(quantities, periods)
            elif method == 'exponential_smoothing':
                forecast, confidence = self.exponential_smoothing_forecast(quantities, periods)
            elif method == 'trend_analysis':
                forecast, confidence = self.trend_analysis_forecast(quantities, periods)
            elif method == 'seasonal':
                forecast, confidence = self.seasonal_forecast(quantities, periods)
            else:  # ensemble
                forecast, confidence = self.ensemble_forecast(quantities, periods)
            
            if forecast is None:
                return None, "Forecasting failed"
            
            # Prepare forecast data
            forecast_data = []
            start_date = datetime.now().replace(day=1)
            
            for i, value in enumerate(forecast):
                period_start = start_date + timedelta(days=30 * i)
                period_end = period_start + timedelta(days=29)
                
                forecast_record = {
                    'product_id': product_id,
                    'warehouse_id': warehouse_id,
                    'period_start': period_start.date(),
                    'period_end': period_end.date(),
                    'predicted_demand': int(round(value)),
                    'forecast_method': method,
                    'confidence_level': round(confidence, 2)
                }
                
                forecast_data.append(forecast_record)
            
            return forecast_data, "Forecast generated successfully"
            
        except Exception as e:
            logging.error(f"Forecast generation error: {str(e)}")
            return None, f"Error generating forecast: {str(e)}"
    
    def evaluate_forecast_accuracy(self, product_id, warehouse_id, method='ensemble'):
        """Evaluate forecast accuracy using historical data"""
        try:
            # Get more historical data for evaluation
            sales_data = ForecastingData.get_sales_history(product_id, warehouse_id, months=36)
            
            if len(sales_data) < 12:
                return None, "Insufficient data for evaluation"
            
            # Split data: use first 24 months for training, last 12 for testing
            train_data = [record['total_quantity'] for record in sales_data[:-12]]
            test_data = [record['total_quantity'] for record in sales_data[-12:]]
            
            # Generate forecast for test period
            forecast, _ = self.generate_forecast(product_id, warehouse_id, 12, method)
            
            if not forecast:
                return None, "Could not generate forecast for evaluation"
            
            # Extract predicted values
            predicted = [record['predicted_demand'] for record in forecast]
            
            # Calculate metrics
            mae = mean_absolute_error(test_data, predicted)
            mse = mean_squared_error(test_data, predicted)
            rmse = np.sqrt(mse)
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((np.array(test_data) - np.array(predicted)) / np.array(test_data))) * 100
            
            accuracy_metrics = {
                'mae': round(mae, 2),
                'mse': round(mse, 2),
                'rmse': round(rmse, 2),
                'mape': round(mape, 2),
                'accuracy_score': max(0, 100 - mape)
            }
            
            return accuracy_metrics, "Evaluation completed"
            
        except Exception as e:
            logging.error(f"Forecast evaluation error: {str(e)}")
            return None, f"Error evaluating forecast: {str(e)}"
