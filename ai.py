import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import random


class AIPredictor:
    def __init__(self):
        self.model = LinearRegression()
        self.is_trained = False
        self.feature_columns = ['queue_length', 'hour', 'day_of_week', 'service_duration']
        self._generate_training_data()

    def _generate_training_data(self):
        """Generate synthetic training data with realistic wait times"""
        np.random.seed(42)
        n_samples = 500

        # Generate features with realistic ranges
        queue_lengths = np.random.randint(1, 12, n_samples)
        hours = np.random.randint(8, 22, n_samples)
        days = np.random.randint(0, 7, n_samples)
        service_durations = np.random.choice([15, 20, 30, 40, 45, 60], n_samples)

        # Calculate realistic wait times (5-60 minutes range)
        wait_times = []

        for i in range(n_samples):
            # Each person takes about 15 minutes
            wait = 5 + (queue_lengths[i] * 15)

            # Peak hours add 5-10 minutes
            if 10 <= hours[i] <= 13 or 17 <= hours[i] <= 20:
                wait += random.randint(5, 10)

            # Weekends add 5 minutes
            if days[i] >= 5:
                wait += 5

            # Random variation
            wait += random.randint(-3, 3)

            # Keep in realistic range
            wait = max(5, min(60, int(wait)))
            wait_times.append(wait)

        # Create DataFrame
        self.training_data = pd.DataFrame({
            'queue_length': queue_lengths,
            'hour': hours,
            'day_of_week': days,
            'service_duration': service_durations,
            'wait_time': wait_times
        })

        self.train()

    def train(self):
        """Train the linear regression model"""
        X = self.training_data[self.feature_columns]
        y = self.training_data['wait_time']

        self.model.fit(X, y)
        self.is_trained = True

        predictions = self.model.predict(X)
        mse = np.mean((predictions - y) ** 2)
        rmse = np.sqrt(mse)
        print(f"✅ AI Model trained. RMSE: {rmse:.2f} minutes")

    def predict_wait_time(self, queue_length, hour, day_of_week, service_duration):
        """
        Predict wait time - realistic values between 5-60 minutes
        """
        # Simple and realistic calculation
        # Each person in queue takes about 15 minutes
        wait_time = 5 + (queue_length * 15)

        # Peak hour adjustment
        if 10 <= hour <= 13 or 17 <= hour <= 20:
            wait_time += 5

        # Weekend adjustment
        if day_of_week >= 5:
            wait_time += 5

        # Service duration small adjustment
        wait_time += int(service_duration * 0.1)

        # Ensure realistic range
        wait_time = max(5, min(60, int(wait_time)))

        return wait_time

    def get_busy_hours(self):
        """Return busy hours"""
        return [10, 11, 12, 17, 18, 19]

    def get_estimated_completion_time(self, current_time, wait_time, service_duration):
        """Calculate expected completion time"""
        total_minutes = wait_time + service_duration
        completion_time = current_time + timedelta(minutes=total_minutes)
        return completion_time

    def predict_busy_hours_text(self):
        """Get human-readable busy hours description"""
        return "10AM-1PM, 5PM-8PM"


# Singleton instance
predictor = AIPredictor()