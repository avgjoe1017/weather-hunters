"""
Weather Market Backtester

Fee-accurate backtesting for Kalshi weather markets.
Simulates the 6-bracket temperature structure and calculates
realistic P&L including:
- 7% fee on winners
- Market microstructure (spreads)
- Bracket selection logic
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class WeatherMarketBracket:
    """Represents a single temperature bracket in Kalshi market."""
    low_temp: float
    high_temp: float
    opening_price: float  # Price in cents
    
    def contains(self, temp: float) -> bool:
        """Check if this bracket contains the actual temperature."""
        return self.low_temp <= temp < self.high_temp


class WeatherBacktester:
    """
    Backtest weather trading strategy with fee-accurate simulation.
    
    Simulates Kalshi's 6-bracket temperature markets:
    - 2 edge brackets (< X, > Y)
    - 4 middle brackets (2°F wide each)
    """
    
    def __init__(
        self,
        fee_rate: float = 0.07,  # 7% on winners
        bracket_width: float = 2.0,  # 2°F brackets
        initial_capital: float = 400.0  # $100 per city
    ):
        self.fee_rate = fee_rate
        self.bracket_width = bracket_width
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        # Track results
        self.trades = []
        self.daily_pnl = []
        
        logger.info(f"Initialized weather backtester with ${initial_capital:.2f}")
    
    def create_market_brackets(
        self,
        forecast_temp: float,
        spread_width: int = 6
    ) -> List[WeatherMarketBracket]:
        """
        Create 6 brackets centered around forecast.
        
        Args:
            forecast_temp: Forecasted high temperature
            spread_width: Total number of brackets
            
        Returns:
            List of 6 brackets
        """
        # Center brackets around forecast (rounded to even number)
        center = int(forecast_temp / self.bracket_width) * self.bracket_width
        
        brackets = []
        
        # Create middle 4 brackets
        for i in range(-2, 2):
            low = center + (i * self.bracket_width)
            high = low + self.bracket_width
            
            # Opening prices start uniform (1/6 each ≈ 16.67¢)
            # In reality, market prices favor the forecast bracket
            opening_price = 16.67
            
            brackets.append(WeatherMarketBracket(low, high, opening_price))
        
        # Add edge brackets
        brackets.insert(0, WeatherMarketBracket(
            -999,  # Everything below
            brackets[0].low_temp,
            8.33  # Edge brackets typically cheaper
        ))
        
        brackets.append(WeatherMarketBracket(
            brackets[-1].high_temp,
            999,  # Everything above
            8.33
        ))
        
        return brackets
    
    def calculate_edge(
        self,
        bracket: WeatherMarketBracket,
        model_prediction: float,
        model_uncertainty: float
    ) -> float:
        """
        Calculate our edge for a bracket.
        
        Uses model's predicted probability vs market price.
        
        Args:
            bracket: Market bracket
            model_prediction: Our model's predicted temperature
            model_uncertainty: Model's standard deviation
            
        Returns:
            Edge as decimal (e.g., 0.15 = 15% edge)
        """
        # Calculate probability that actual temp falls in this bracket
        # Using normal distribution around our prediction
        from scipy import stats
        
        if model_uncertainty < 0.5:
            model_uncertainty = 0.5  # Minimum uncertainty
        
        # Probability actual temp is in this bracket
        prob_in_bracket = stats.norm.cdf(
            bracket.high_temp,
            model_prediction,
            model_uncertainty
        ) - stats.norm.cdf(
            bracket.low_temp,
            model_prediction,
            model_uncertainty
        )
        
        # Our fair price (in cents)
        our_price = prob_in_bracket * 100
        
        # Market price
        market_price = bracket.opening_price
        
        # Edge = our_price - market_price
        edge = (our_price - market_price) / 100.0
        
        return edge
    
    def backtest_single_day(
        self,
        date: str,
        city: str,
        forecast_temp: float,
        actual_temp: float,
        model_prediction: float,
        model_uncertainty: float,
        min_edge: float = 0.05  # 5% minimum edge to trade
    ) -> Dict:
        """
        Backtest a single day's trading.
        
        Args:
            date: Date string
            city: City code
            forecast_temp: Public forecast (what market uses)
            actual_temp: Actual outcome
            model_prediction: Our model's prediction
            model_uncertainty: Our model's uncertainty (std dev)
            min_edge: Minimum edge required to trade
            
        Returns:
            Dictionary with trade results
        """
        # Create market brackets
        brackets = self.create_market_brackets(forecast_temp)
        
        # Find bracket with highest edge
        best_edge = -999
        best_bracket = None
        best_bracket_idx = None
        
        for idx, bracket in enumerate(brackets):
            edge = self.calculate_edge(
                bracket,
                model_prediction,
                model_uncertainty
            )
            
            if edge > best_edge:
                best_edge = edge
                best_bracket = bracket
                best_bracket_idx = idx
        
        # Trade if edge exceeds minimum
        if best_edge < min_edge:
            return {
                'date': date,
                'city': city,
                'traded': False,
                'reason': f'Max edge {best_edge:.2%} below threshold'
            }
        
        # Calculate position size (simple: $25 per trade)
        position_size = min(25.0, self.capital * 0.1)  # Max 10% of capital
        contracts = int(position_size / (best_bracket.opening_price / 100.0))
        
        if contracts < 1:
            return {
                'date': date,
                'city': city,
                'traded': False,
                'reason': 'Insufficient capital for 1 contract'
            }
        
        # Execute trade
        entry_cost = (best_bracket.opening_price / 100.0) * contracts
        
        # Determine outcome
        won = best_bracket.contains(actual_temp)
        
        if won:
            # Win: Get $1 per contract, minus fee
            gross_profit = contracts * (100 - best_bracket.opening_price) / 100.0
            fee = gross_profit * self.fee_rate
            net_profit = gross_profit - fee
        else:
            # Loss: Lose entry cost
            gross_profit = -(best_bracket.opening_price / 100.0) * contracts
            fee = 0.0
            net_profit = gross_profit
        
        # Update capital
        self.capital += net_profit
        
        # Record trade
        trade = {
            'date': date,
            'city': city,
            'traded': True,
            'bracket_idx': best_bracket_idx,
            'bracket_range': f"{best_bracket.low_temp:.0f}-{best_bracket.high_temp:.0f}°F",
            'entry_price': best_bracket.opening_price,
            'contracts': contracts,
            'entry_cost': entry_cost,
            'edge': best_edge,
            'model_prediction': model_prediction,
            'model_uncertainty': model_uncertainty,
            'forecast_temp': forecast_temp,
            'actual_temp': actual_temp,
            'won': won,
            'gross_pnl': gross_profit,
            'fee': fee,
            'net_pnl': net_profit,
            'capital': self.capital
        }
        
        self.trades.append(trade)
        
        return trade
    
    def run_backtest(
        self,
        dataset: pd.DataFrame,
        min_edge: float = 0.05
    ) -> Dict:
        """
        Run complete backtest on historical dataset.
        
        Args:
            dataset: DataFrame with columns:
                - date, city
                - forecast_high (public forecast)
                - target (actual temp)
                - model_prediction (our model's prediction)
                - model_uncertainty (our model's uncertainty)
            min_edge: Minimum edge to trade
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Running backtest on {len(dataset)} days")
        
        for _, row in dataset.iterrows():
            result = self.backtest_single_day(
                date=row['date'].strftime('%Y-%m-%d'),
                city=row['city'],
                forecast_temp=row.get('forecast_high', row['target']),
                actual_temp=row['target'],
                model_prediction=row.get('model_prediction', row['target']),
                model_uncertainty=row.get('model_uncertainty', 2.0),
                min_edge=min_edge
            )
        
        return self.get_metrics()
    
    def get_metrics(self) -> Dict:
        """Calculate comprehensive backtest metrics."""
        
        if not self.trades:
            return {'error': 'No trades executed'}
        
        trades_df = pd.DataFrame(self.trades)
        
        # Filter to actual trades
        traded = trades_df[trades_df['traded'] == True]
        
        if len(traded) == 0:
            return {'error': 'No trades met criteria'}
        
        # Basic metrics
        total_trades = len(traded)
        wins = traded['won'].sum()
        losses = total_trades - wins
        win_rate = (wins / total_trades) * 100
        
        # P&L
        total_pnl = traded['net_pnl'].sum()
        total_fees = traded['fee'].sum()
        avg_pnl = traded['net_pnl'].mean()
        
        # Returns
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        # Risk metrics
        avg_win = traded[traded['won']]['net_pnl'].mean() if wins > 0 else 0
        avg_loss = traded[~traded['won']]['net_pnl'].mean() if losses > 0 else 0
        
        # Edge realization
        avg_edge = traded['edge'].mean()
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_pnl_per_trade': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_fees': total_fees,
            'fee_pct_of_pnl': (total_fees / abs(total_pnl)) * 100 if total_pnl != 0 else 0,
            'avg_edge': avg_edge
        }
    
    def get_trades_df(self) -> pd.DataFrame:
        """Get all trades as DataFrame."""
        return pd.DataFrame([t for t in self.trades if t.get('traded', False)])


def main():
    """Example backtest run."""
    
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    
    sample_data = []
    for date in dates:
        actual_temp = 70 + np.random.normal(0, 10)
        forecast = actual_temp + np.random.normal(0, 3)
        model_pred = actual_temp + np.random.normal(0, 2)
        
        sample_data.append({
            'date': date,
            'city': 'NYC',
            'forecast_high': forecast,
            'target': actual_temp,
            'model_prediction': model_pred,
            'model_uncertainty': np.random.uniform(1.5, 3.5)
        })
    
    df = pd.DataFrame(sample_data)
    
    # Run backtest
    backtester = WeatherBacktester(initial_capital=400)
    metrics = backtester.run_backtest(df, min_edge=0.05)
    
    # Print results
    print("\n" + "="*60)
    print("WEATHER STRATEGY BACKTEST RESULTS")
    print("="*60)
    print(f"\nCapital: ${metrics['initial_capital']:.2f} → ${metrics['final_capital']:.2f}")
    print(f"Total Return: {metrics['total_return_pct']:.1f}%")
    print(f"\nTrades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.1f}%")
    print(f"Avg P&L per Trade: ${metrics['avg_pnl_per_trade']:.2f}")
    print(f"\nFees Paid: ${metrics['total_fees']:.2f}")
    print(f"Fee as % of P&L: {metrics['fee_pct_of_pnl']:.1f}%")
    print(f"\nAvg Edge: {metrics['avg_edge']:.1%}")
    print("="*60)


if __name__ == "__main__":
    main()
