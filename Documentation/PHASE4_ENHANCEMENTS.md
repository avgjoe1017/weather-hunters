# Phase 4 Enhancements: Advanced Features

## Overview

This document outlines advanced features for Phase 4+ that will further improve edge detection and execution quality.

---

## 1. Order Book & Liquidity as Features

### The Core Insight

**Price tells you "what" - Liquidity tells you "how confident"**

A 90¢ price could mean:
- **High confidence**: 89¢ bid / 90¢ ask with 1000 contracts on each side
- **Low confidence**: 75¢ bid / 95¢ ask with 10 contracts total

The second case is an illiquid, uncertain market - not a real "favorite."

### Why This Matters for FLB Strategy

The Favorite-Longshot Bias is strongest in **liquid, confident markets**:
- ✅ **Tight spread + high volume** = Real favorite = Strong FLB signal
- ⚠️ **Wide spread + low volume** = Uncertain price = Weak FLB signal

### Implementation Design

#### Feature Engineering

```python
@dataclass
class LiquidityFeatures:
    """Liquidity-based features for ML models"""
    
    # Spread metrics
    bid_ask_spread_cents: float
    bid_ask_spread_pct: float
    bid_ask_spread_bps: float
    
    # Volume metrics
    total_volume: int
    bid_size: int
    ask_size: int
    bid_ask_ratio: float  # Bid size / ask size
    
    # Depth metrics
    depth_5_levels: int  # Sum of size in top 5 levels
    depth_imbalance: float  # (Bid depth - Ask depth) / Total depth
    
    # Quality score
    liquidity_score: float  # Composite 0-1 score
    
    def calculate_liquidity_score(self) -> float:
        """
        Calculate composite liquidity score.
        
        High score = tight spread + high volume = trustworthy price
        Low score = wide spread + low volume = unreliable price
        """
        # Spread component (lower is better)
        spread_score = max(0, 1 - (self.bid_ask_spread_bps / 200))  # 200 bps = 0
        
        # Volume component (higher is better)
        # Normalize to typical market size (1000 contracts)
        volume_score = min(1, self.total_volume / 1000)
        
        # Balance component (closer to 1:1 is better)
        balance_score = 1 - abs(self.bid_ask_ratio - 1.0) / 2
        
        # Weighted combination
        return (
            0.5 * spread_score +
            0.3 * volume_score +
            0.2 * balance_score
        )


def extract_orderbook_features(orderbook: Dict) -> LiquidityFeatures:
    """
    Extract liquidity features from Kalshi orderbook.
    
    Args:
        orderbook: Orderbook from Kalshi API
        
    Returns:
        LiquidityFeatures object
    """
    yes_bids = orderbook.get('yes', [])
    yes_asks = orderbook.get('no', [])  # Buying NO = selling YES
    
    if not yes_bids or not yes_asks:
        # No liquidity - return worst case
        return LiquidityFeatures(
            bid_ask_spread_cents=100,
            bid_ask_spread_pct=100,
            bid_ask_spread_bps=10000,
            total_volume=0,
            bid_size=0,
            ask_size=0,
            bid_ask_ratio=0,
            depth_5_levels=0,
            depth_imbalance=0,
            liquidity_score=0
        )
    
    # Best bid/ask
    best_bid_price, best_bid_size = yes_bids[0]
    best_ask_price, best_ask_size = yes_asks[0]
    
    # Spread calculations
    spread_cents = best_ask_price - best_bid_price
    mid_price = (best_bid_price + best_ask_price) / 2
    spread_pct = (spread_cents / mid_price) * 100 if mid_price > 0 else 100
    spread_bps = (spread_cents / mid_price) * 10000 if mid_price > 0 else 10000
    
    # Volume calculations
    bid_size = sum(size for _, size in yes_bids[:5])  # Top 5 levels
    ask_size = sum(size for _, size in yes_asks[:5])
    total_volume = bid_size + ask_size
    bid_ask_ratio = bid_size / ask_size if ask_size > 0 else 0
    
    # Depth calculations
    depth_5_levels = bid_size + ask_size
    depth_imbalance = (bid_size - ask_size) / (bid_size + ask_size) if (bid_size + ask_size) > 0 else 0
    
    features = LiquidityFeatures(
        bid_ask_spread_cents=spread_cents,
        bid_ask_spread_pct=spread_pct,
        bid_ask_spread_bps=spread_bps,
        total_volume=total_volume,
        bid_size=bid_size,
        ask_size=ask_size,
        bid_ask_ratio=bid_ask_ratio,
        depth_5_levels=depth_5_levels,
        depth_imbalance=depth_imbalance,
        liquidity_score=0  # Will be calculated
    )
    
    features.liquidity_score = features.calculate_liquidity_score()
    
    return features
```

#### Integration into FLB Strategy

```python
class FLBHarvesterV2:
    """Enhanced FLB strategy with liquidity filtering"""
    
    def _evaluate_market(self, market: Dict) -> Optional[Dict]:
        """
        Evaluate market with liquidity quality check.
        """
        ticker = market.get("ticker")
        
        # Get orderbook
        orderbook = self.api.get_orderbook(ticker)
        
        # Extract liquidity features
        liquidity = extract_orderbook_features(orderbook)
        
        # CRITICAL: Filter by liquidity score
        if liquidity.liquidity_score < 0.3:  # Minimum quality threshold
            logger.debug(f"Rejected {ticker}: low liquidity score ({liquidity.liquidity_score:.2f})")
            return None
        
        # Also check spread explicitly
        if liquidity.bid_ask_spread_bps > 200:  # 200 bps max
            logger.debug(f"Rejected {ticker}: wide spread ({liquidity.bid_ask_spread_bps:.0f} bps)")
            return None
        
        # Check volume
        if liquidity.total_volume < 50:  # Minimum 50 contracts
            logger.debug(f"Rejected {ticker}: low volume ({liquidity.total_volume})")
            return None
        
        # Now evaluate FLB opportunity as before
        yes_price = (liquidity.best_bid_price + liquidity.best_ask_price) / 2
        
        # ... rest of FLB logic ...
        
        # Include liquidity score in signal
        if signal:
            signal['liquidity_score'] = liquidity.liquidity_score
            signal['spread_bps'] = liquidity.bid_ask_spread_bps
            
            # Adjust edge based on liquidity confidence
            # Higher liquidity = higher confidence = can use edge more aggressively
            signal['edge_adjusted'] = signal['edge'] * liquidity.liquidity_score
        
        return signal
```

#### Integration into Hybrid ML Model (Strategy B)

```python
def prepare_features_for_ml(
    ticker: str,
    orderbook: Dict,
    weather_forecasts: Dict
) -> Dict[str, float]:
    """
    Prepare features for hybrid ML model including liquidity.
    """
    # Weather features
    features = {
        'noaa_forecast_prob': weather_forecasts['noaa'],
        'ecmwf_forecast_prob': weather_forecasts['ecmwf'],
        'model_disagreement': weather_forecasts['disagreement'],
        'historical_avg': weather_forecasts['historical_avg'],
    }
    
    # Market price feature
    mid_price = (orderbook['best_bid'] + orderbook['best_ask']) / 2
    features['market_price'] = mid_price
    
    # LIQUIDITY FEATURES (NEW)
    liquidity = extract_orderbook_features(orderbook)
    features['liquidity_score'] = liquidity.liquidity_score
    features['bid_ask_spread_bps'] = liquidity.bid_ask_spread_bps
    features['total_volume'] = liquidity.total_volume
    features['depth_imbalance'] = liquidity.depth_imbalance
    
    return features


# The ML model learns:
# 1. When market_price is 90¢ AND liquidity_score > 0.8
#    → Strong FLB signal, trust the price
# 2. When market_price is 90¢ AND liquidity_score < 0.3
#    → Weak signal, price may be noise
# 3. Weather signals are more valuable when liquidity is low
#    (market hasn't formed consensus yet)
```

### Expected Impact

**Filtering Effect:**
- **Before:** Trade all markets with price ≥ 90¢
- **After:** Trade only markets with price ≥ 90¢ AND liquidity_score ≥ 0.3

**Performance Improvements:**
- **Higher win rate** - Eliminates false favorites (illiquid markets)
- **Lower slippage** - Only trade liquid markets with tight spreads
- **Better fills** - Sufficient volume to execute at reasonable prices
- **Fewer traps** - Avoid markets where price is unreliable

**Backtesting Validation:**
```python
# Compare strategies
results_baseline = backtest_flb(
    use_liquidity_filter=False
)

results_enhanced = backtest_flb(
    use_liquidity_filter=True,
    min_liquidity_score=0.3
)

print("Baseline FLB:")
print(f"  Win rate: {results_baseline['win_rate']:.1f}%")
print(f"  Avg slippage: {results_baseline['avg_slippage']:.1f} bps")

print("\nLiquidity-Filtered FLB:")
print(f"  Win rate: {results_enhanced['win_rate']:.1f}%")  # Expected +3-5%
print(f"  Avg slippage: {results_enhanced['avg_slippage']:.1f} bps")  # Expected -50%
print(f"  Trades filtered: {results_baseline['trades'] - results_enhanced['trades']}")
```

---

## 2. Advanced Order Management

### Intelligent Order Placement

```python
class SmartOrderManager:
    """
    Advanced order management with:
    - Jittered re-pricing
    - Partial fill handling
    - Adaptive spread crossing
    """
    
    def place_smart_order(
        self,
        ticker: str,
        side: str,
        contracts: int,
        max_price_cents: int,
        urgency: float = 0.5
    ) -> Order:
        """
        Place order with intelligent pricing.
        
        Args:
            urgency: 0 = patient (passive), 1 = urgent (aggressive)
        """
        orderbook = self.api.get_orderbook(ticker)
        liquidity = extract_orderbook_features(orderbook)
        
        if urgency < 0.3:
            # Patient - join the bid/ask
            if side == "yes":
                price = orderbook['best_bid'] + 1  # Just above best bid
            else:
                price = orderbook['best_ask'] - 1
        
        elif urgency > 0.7:
            # Urgent - cross the spread
            if side == "yes":
                price = orderbook['best_ask']  # Take the ask
            else:
                price = orderbook['best_bid']
        
        else:
            # Moderate - split the spread
            mid = (orderbook['best_bid'] + orderbook['best_ask']) / 2
            price = int(mid) + np.random.randint(-1, 2)  # Jitter
        
        # Cap at max price
        price = min(price, max_price_cents)
        
        return self.api.create_order(
            ticker=ticker,
            side=side,
            action="buy",
            count=contracts,
            type="limit",
            yes_price=price if side == "yes" else None,
            no_price=price if side == "no" else None
        )
```

---

## 3. Market Microstructure Features

### Additional Signals from Order Flow

```python
@dataclass
class MicrostructureFeatures:
    """Advanced market microstructure signals"""
    
    # Order flow
    recent_trade_direction: float  # Net buying (+) or selling (-)
    trade_intensity: float  # Trades per minute
    volume_weighted_price: float  # VWAP
    
    # Price action
    price_momentum_5min: float
    price_volatility_15min: float
    
    # Orderbook dynamics
    bid_ask_ratio_change: float  # Is the ratio shifting?
    orderbook_resilience: float  # How quickly does it refill after trades?
    
    def indicates_informed_trading(self) -> bool:
        """
        Detect if there's informed trading activity.
        
        Signs of informed trading:
        - Persistent one-sided flow
        - Large trades with minimal market impact
        - Rapid orderbook refill after trades
        """
        return (
            abs(self.recent_trade_direction) > 0.6 and  # One-sided
            self.orderbook_resilience > 0.7 and  # Quick refill
            self.trade_intensity > 2.0  # Active trading
        )
```

### Usage in Strategy

```python
def should_trade_with_microstructure(
    market: Dict,
    orderbook: Dict,
    recent_trades: List[Dict]
) -> bool:
    """
    Enhanced decision using microstructure.
    """
    # Extract features
    liquidity = extract_orderbook_features(orderbook)
    microstructure = extract_microstructure_features(recent_trades, orderbook)
    
    # Don't trade against informed flow
    if microstructure.indicates_informed_trading():
        if microstructure.recent_trade_direction > 0.6:
            # Smart money is buying - don't fade it
            logger.info(f"Detected informed buying on {market['ticker']}")
            return False
    
    # Prefer markets with stable orderbooks
    if liquidity.liquidity_score > 0.7 and microstructure.orderbook_resilience > 0.6:
        return True
    
    return False
```

---

## 4. Implementation Priority

### Phase 4A: Liquidity Features (1 week)
- [ ] Implement `extract_orderbook_features()`
- [ ] Add liquidity filtering to FLB strategy
- [ ] Backtest with/without liquidity filter
- [ ] Measure impact on win rate and slippage
- [ ] Deploy to demo environment

### Phase 4B: Smart Order Management (1 week)
- [ ] Implement `SmartOrderManager`
- [ ] Add jittered pricing logic
- [ ] Test partial fill handling
- [ ] Measure fill ratio improvement
- [ ] Deploy to production

### Phase 4C: Microstructure Analysis (2 weeks)
- [ ] Implement trade flow tracking
- [ ] Add momentum and volatility features
- [ ] Build informed trading detector
- [ ] Backtest with microstructure signals
- [ ] Integrate into hybrid model

---

## 5. Expected Results

### Liquidity Filtering
- **Win rate:** +3-5 percentage points
- **Slippage:** -30-50% reduction
- **Edge confidence:** Higher (fewer false signals)
- **Trade volume:** -20-30% (but higher quality)

### Smart Order Management
- **Fill ratio:** +10-15 percentage points
- **Average price:** -2-3 bps improvement
- **Execution quality:** Significantly better

### Microstructure Features
- **Edge detection:** More nuanced (know when to sit out)
- **Timing:** Better entry/exit points
- **Risk management:** Avoid trading against informed flow

---

## 6. Code Structure

```
src/
├── features/
│   ├── liquidity.py           # Orderbook feature extraction
│   ├── microstructure.py      # Trade flow analysis
│   └── feature_store.py       # Feature persistence
├── execution/
│   ├── smart_order_mgr.py     # Intelligent order placement
│   ├── fill_tracker.py        # Fill ratio monitoring
│   └── slippage_optimizer.py  # Minimize execution costs
└── analysis/
    ├── liquidity_study.ipynb  # Liquidity impact analysis
    └── microstructure_study.ipynb
```

---

## 7. Final Notes

**Liquidity features are a natural extension because:**
1. They're already in the Kalshi API (no new data needed)
2. They directly address a weakness (illiquid "favorites" are noise)
3. They improve the existing FLB strategy immediately
4. They integrate seamlessly into the hybrid ML model

**Start with liquidity filtering** - it's the highest ROI feature you can add with minimal complexity. The microstructure features are more advanced and can come later.

**Remember:** Better to trade 70% of markets with 60% win rate than 100% of markets with 55% win rate.
