"""
Trading System Risks - Educational Simulation
==================================================
This script demonstrates 3 critical technical problems in algorithmic trading
and how to fix them.

For Students: Run each demo to see BEFORE (bad code) vs AFTER (fixed code)

Author: Quantitative Trading Course
Purpose: Teaching System Risk Management
"""

import time
import random
from datetime import datetime
from typing import Dict, Optional


# ============================================================================
# PROBLEM 1: DOUBLE ORDER EXECUTION (Race Condition / Network Timeout)
# ============================================================================

def demo_double_order_bad():
    """
    ❌ BAD IMPLEMENTATION
    
    Problem: Network timeout causes retry without tracking order ID
    Result: Exchange processes BOTH orders → Double position!
    """
    print("\n" + "="*70)
    print("🔴 PROBLEM 1: DOUBLE ORDER (BAD IMPLEMENTATION)")
    print("="*70)
    
    def place_order_bad(symbol, quantity, price):
        """Simulates placing order WITHOUT idempotency key"""
        print(f"\n>>> Sending order: BUY {quantity} {symbol} @ ${price}")
        
        # Simulate network delay
        time.sleep(0.5)
        
        # Simulate random network timeout (50% chance)
        if random.random() < 0.5:
            print("⏳ Network timeout! No ACK received...")
            print("⚠️  Bot retries immediately (BAD PRACTICE!)")
            time.sleep(0.3)
            
            # Retry without checking if first order went through
            print(f">>> [RETRY] Sending order: BUY {quantity} {symbol} @ ${price}")
            time.sleep(0.5)
            
            # Exchange actually processed BOTH orders!
            print("✅ Order #1 FILLED (from first attempt)")
            print("✅ Order #2 FILLED (from retry)")
            print("💥 DISASTER: You now have DOUBLE the position you wanted!")
            
            return {"orders_filled": 2, "total_quantity": quantity * 2}
        else:
            print("✅ Order FILLED normally")
            return {"orders_filled": 1, "total_quantity": quantity}
    
    # Simulate trading
    intended_position = 1.0  # Want to buy 1 BTC
    result = place_order_bad("BTC", intended_position, 50000)
    
    print(f"\n📊 RESULT:")
    print(f"   Intended: {intended_position} BTC")
    print(f"   Actually got: {result['total_quantity']} BTC")
    
    if result['orders_filled'] > 1:
        print(f"   ❌ OVER-EXPOSED BY: {result['total_quantity'] - intended_position} BTC")
        print(f"   💸 Extra risk: ${(result['total_quantity'] - intended_position) * 50000:,.0f}")


def demo_double_order_fixed():
    """
    ✅ FIXED IMPLEMENTATION
    
    Solution: Use Client Order ID (Idempotency Key)
    Result: Exchange recognizes retry as duplicate → Processes only once
    """
    print("\n" + "="*70)
    print("✅ SOLUTION 1: IDEMPOTENCY KEY (FIXED IMPLEMENTATION)")
    print("="*70)
    
    # Simulate exchange's order tracking
    exchange_processed_orders = set()
    
    def place_order_fixed(symbol, quantity, price, client_order_id):
        """Simulates placing order WITH idempotency key"""
        print(f"\n>>> Sending order: BUY {quantity} {symbol} @ ${price}")
        print(f"    🔑 Client Order ID: {client_order_id}")
        
        # Simulate network delay
        time.sleep(0.5)
        
        # Simulate random network timeout (50% chance)
        if random.random() < 0.5:
            print("⏳ Network timeout! No ACK received...")
            print("⚠️  Bot retries with SAME Client Order ID")
            time.sleep(0.3)
            
            # Retry with same Client Order ID
            print(f">>> [RETRY] Sending order: BUY {quantity} {symbol} @ ${price}")
            print(f"    🔑 Client Order ID: {client_order_id} (SAME)")
            time.sleep(0.5)
            
            # Exchange checks if this order was already processed
            if client_order_id in exchange_processed_orders:
                print("🛡️  Exchange: 'This order ID already processed, ignoring retry'")
                print("✅ Order #1 FILLED (original)")
                print("🚫 Order #2 REJECTED (duplicate detected)")
            else:
                # First time seeing this order
                exchange_processed_orders.add(client_order_id)
                print("✅ Order FILLED")
            
            return {"orders_filled": 1, "total_quantity": quantity}
        else:
            # Normal execution
            exchange_processed_orders.add(client_order_id)
            print("✅ Order FILLED normally")
            return {"orders_filled": 1, "total_quantity": quantity}
    
    # Simulate trading with unique order ID
    intended_position = 1.0
    unique_order_id = f"ORDER_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
    
    result = place_order_fixed("BTC", intended_position, 50000, unique_order_id)
    
    print(f"\n📊 RESULT:")
    print(f"   Intended: {intended_position} BTC")
    print(f"   Actually got: {result['total_quantity']} BTC")
    print(f"   ✅ Position matches intention - SAFE!")


# ============================================================================
# PROBLEM 2: SLIPPAGE DUE TO LATENCY
# ============================================================================

def demo_slippage_bad():
    """
    ❌ BAD IMPLEMENTATION
    
    Problem: Using Market Order with latency
    Result: Price moves significantly before execution
    """
    print("\n" + "="*70)
    print("🔴 PROBLEM 2: SLIPPAGE (BAD IMPLEMENTATION)")
    print("="*70)
    
    # Simulate current market price
    current_price = 100.0
    print(f"\n📊 Bot sees BUY signal at price: ${current_price}")
    
    def place_market_order_bad(symbol, quantity):
        """Places a MARKET ORDER (accepts any price)"""
        print(f"\n>>> Sending MARKET ORDER: BUY {quantity} {symbol}")
        print("    ⚠️  No price protection!")
        
        # Simulate network latency (200ms)
        print("⏳ Network latency: 200ms...")
        time.sleep(0.2)
        
        # During latency, price moved up (simulating volatile market)
        price_movement = random.uniform(3, 8)  # Price jumps 3-8%
        executed_price = current_price * (1 + price_movement/100)
        
        print(f"💨 Price moved during latency!")
        print(f"✅ Order FILLED at: ${executed_price:.2f}")
        
        slippage_pct = ((executed_price - current_price) / current_price) * 100
        slippage_cost = (executed_price - current_price) * quantity
        
        return {
            "intended_price": current_price,
            "executed_price": executed_price,
            "slippage_pct": slippage_pct,
            "slippage_cost": slippage_cost
        }
    
    # Execute trade
    result = place_market_order_bad("BTC", 10)
    
    print(f"\n📊 RESULT:")
    print(f"   Expected price: ${result['intended_price']:.2f}")
    print(f"   Actual fill: ${result['executed_price']:.2f}")
    print(f"   ❌ Slippage: {result['slippage_pct']:.2f}%")
    print(f"   💸 Extra cost: ${result['slippage_cost']:.2f}")


def demo_slippage_fixed():
    """
    ✅ FIXED IMPLEMENTATION
    
    Solution: Use Limit Order with slippage tolerance
    Result: Order only executes within acceptable price range
    """
    print("\n" + "="*70)
    print("✅ SOLUTION 2: LIMIT ORDER (FIXED IMPLEMENTATION)")
    print("="*70)
    
    current_price = 100.0
    print(f"\n📊 Bot sees BUY signal at price: ${current_price}")
    
    def place_limit_order_fixed(symbol, quantity, max_price):
        """Places a LIMIT ORDER with maximum acceptable price"""
        print(f"\n>>> Sending LIMIT ORDER: BUY {quantity} {symbol}")
        print(f"    🛡️  Max acceptable price: ${max_price:.2f}")
        print(f"    📏 Slippage tolerance: {((max_price/current_price - 1) * 100):.2f}%")
        
        # Simulate network latency
        print("⏳ Network latency: 200ms...")
        time.sleep(0.2)
        
        # Price moves during latency
        price_movement = random.uniform(3, 8)
        market_price = current_price * (1 + price_movement/100)
        
        print(f"💨 Current market price: ${market_price:.2f}")
        
        # Exchange checks if market price is within limit
        if market_price <= max_price:
            print(f"✅ Order FILLED at: ${market_price:.2f}")
            print(f"    ✅ Within acceptable range!")
            
            slippage_pct = ((market_price - current_price) / current_price) * 100
            slippage_cost = (market_price - current_price) * quantity
            
            return {
                "status": "filled",
                "intended_price": current_price,
                "executed_price": market_price,
                "slippage_pct": slippage_pct,
                "slippage_cost": slippage_cost
            }
        else:
            print(f"🚫 Order REJECTED!")
            print(f"    Market price ${market_price:.2f} > Limit ${max_price:.2f}")
            print(f"    🛡️  Protected from {((market_price/max_price - 1) * 100):.2f}% excessive slippage")
            
            return {
                "status": "rejected",
                "intended_price": current_price,
                "market_price": market_price,
                "limit_price": max_price
            }
    
    # Execute trade with 1% slippage tolerance
    slippage_tolerance = 0.01  # 1%
    max_acceptable_price = current_price * (1 + slippage_tolerance)
    
    result = place_limit_order_fixed("BTC", 10, max_acceptable_price)
    
    print(f"\n📊 RESULT:")
    if result['status'] == 'filled':
        print(f"   Expected: ${result['intended_price']:.2f}")
        print(f"   Filled at: ${result['executed_price']:.2f}")
        print(f"   Slippage: {result['slippage_pct']:.2f}%")
        print(f"   ✅ Within tolerance - SAFE!")
    else:
        print(f"   Expected: ${result['intended_price']:.2f}")
        print(f"   Market moved to: ${result['market_price']:.2f}")
        print(f"   Limit was: ${result['limit_price']:.2f}")
        print(f"   ✅ Avoided bad fill - PROTECTED!")


# ============================================================================
# PROBLEM 3: NETWORK INSTABILITY (High Ping / Disconnect)
# ============================================================================

def demo_network_instability_bad():
    """
    ❌ BAD IMPLEMENTATION
    
    Problem: No network quality check before trading
    Result: Orders during high latency → unpredictable fills
    """
    print("\n" + "="*70)
    print("🔴 PROBLEM 3: NETWORK INSTABILITY (BAD IMPLEMENTATION)")
    print("="*70)
    
    def check_network_and_trade_bad():
        """Trading logic WITHOUT network health check"""
        print("\n🤖 Trading Bot Started")
        
        for i in range(5):
            print(f"\n--- Cycle {i+1} ---")
            
            # Simulate random network conditions
            ping = random.randint(20, 500)  # ms
            
            # Bot doesn't check network quality!
            print(f"📡 Current ping: {ping}ms")
            
            # Bot blindly tries to trade
            print(f"🎯 Signal detected: BUY")
            
            if ping > 200:
                print(f"⚠️  High latency detected ({ping}ms) but bot continues anyway!")
                print(f">>> Sending order...")
                time.sleep(0.3)
                print(f"❌ Order executed with {random.randint(5, 15)}% unexpected slippage!")
                print(f"💥 Filled at much worse price due to latency")
            elif ping > 400:
                print(f"💥 Connection unstable! Order may fail or execute incorrectly")
                print(f">>> Sending order...")
                time.sleep(0.5)
                if random.random() < 0.5:
                    print(f"❌ ORDER TIMEOUT - No confirmation received!")
                    print(f"⚠️  Don't know if order was filled or not - DANGEROUS!")
                else:
                    print(f"⚠️  Order filled but at unpredictable price")
            else:
                print(f">>> Sending order...")
                time.sleep(0.1)
                print(f"✅ Order filled normally")
            
            time.sleep(0.5)
    
    check_network_and_trade_bad()
    
    print(f"\n📊 RESULT:")
    print(f"   ❌ Bot traded regardless of network quality")
    print(f"   💥 High risk of bad fills, timeouts, unknown state")


def demo_network_instability_fixed():
    """
    ✅ FIXED IMPLEMENTATION
    
    Solution: Circuit Breaker pattern - Monitor network health
    Result: Trading pauses when network is unstable
    """
    print("\n" + "="*70)
    print("✅ SOLUTION 3: CIRCUIT BREAKER (FIXED IMPLEMENTATION)")
    print("="*70)
    
    class CircuitBreaker:
        """
        Circuit Breaker: Prevents trading when network is unstable
        
        States:
        - CLOSED: Normal operation (trading allowed)
        - OPEN: Circuit tripped (trading blocked)
        """
        
        def __init__(self, max_ping_ms=200, failure_threshold=2):
            self.max_ping_ms = max_ping_ms
            self.failure_threshold = failure_threshold
            self.failure_count = 0
            self.is_open = False
        
        def check_network(self, ping_ms):
            """Check if network is healthy enough for trading"""
            
            if ping_ms > self.max_ping_ms:
                self.failure_count += 1
                print(f"    ⚠️  High ping detected: {ping_ms}ms (threshold: {self.max_ping_ms}ms)")
                
                if self.failure_count >= self.failure_threshold:
                    if not self.is_open:
                        self.is_open = True
                        print(f"    🚨 CIRCUIT BREAKER OPENED - Trading PAUSED")
                    return False
            else:
                # Good network - reset counter
                if self.failure_count > 0:
                    print(f"    ✅ Network recovered")
                
                self.failure_count = 0
                
                if self.is_open:
                    self.is_open = False
                    print(f"    ✅ CIRCUIT BREAKER CLOSED - Trading RESUMED")
            
            return not self.is_open
    
    def check_network_and_trade_fixed():
        """Trading logic WITH circuit breaker protection"""
        print("\n🤖 Trading Bot Started (with Circuit Breaker)")
        
        circuit_breaker = CircuitBreaker(max_ping_ms=200, failure_threshold=2)
        
        for i in range(5):
            print(f"\n--- Cycle {i+1} ---")
            
            # Measure network quality
            ping = random.randint(20, 500)
            print(f"📡 Checking network health...")
            print(f"    Current ping: {ping}ms")
            
            # Check circuit breaker
            network_ok = circuit_breaker.check_network(ping)
            
            # Trading signal
            print(f"🎯 Signal detected: BUY")
            
            if network_ok:
                print(f">>> Network quality OK - Sending order...")
                time.sleep(0.1)
                print(f"✅ Order filled successfully")
            else:
                print(f"🛡️  Circuit breaker is OPEN - Skipping trade")
                print(f"    Reason: Network too unstable (ping > 200ms)")
                print(f"    🛡️  PROTECTED from bad execution")
            
            time.sleep(0.5)
    
    check_network_and_trade_fixed()
    
    print(f"\n📊 RESULT:")
    print(f"   ✅ Bot only trades when network is stable")
    print(f"   🛡️  Circuit breaker prevents risky executions")
    print(f"   ✅ System is RESILIENT to network issues")


# ============================================================================
# MAIN DEMO RUNNER
# ============================================================================

def run_all_demos():
    """Run all demonstrations"""
    
    print("\n" + "="*70)
    print("🎓 TRADING SYSTEM RISKS - EDUCATIONAL DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows 3 critical technical problems and their solutions:")
    print("1. Double Order Execution (Network Timeout)")
    print("2. Slippage due to Latency")
    print("3. Network Instability")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start Demo 1: Double Order Problem...")
    demo_double_order_bad()
    
    input("\n\nPress ENTER to see the FIX for Demo 1...")
    demo_double_order_fixed()
    
    input("\n\nPress ENTER to start Demo 2: Slippage Problem...")
    demo_slippage_bad()
    
    input("\n\nPress ENTER to see the FIX for Demo 2...")
    demo_slippage_fixed()
    
    input("\n\nPress ENTER to start Demo 3: Network Instability Problem...")
    demo_network_instability_bad()
    
    input("\n\nPress ENTER to see the FIX for Demo 3...")
    demo_network_instability_fixed()
    
    print("\n" + "="*70)
    print("✅ ALL DEMONSTRATIONS COMPLETED!")
    print("="*70)
    print("\n🎓 KEY TAKEAWAYS FOR STUDENTS:")
    print("\n1. DOUBLE ORDERS:")
    print("   -> Always use Client Order ID (Idempotency Key)")
    print("   -> Exchange can detect and reject duplicate orders")
    print("\n2. SLIPPAGE:")
    print("   -> Avoid blind Market Orders in volatile markets")
    print("   -> Use Limit Orders with acceptable price range")
    print("\n3. NETWORK ISSUES:")
    print("   -> Implement Circuit Breaker pattern")
    print("   -> Monitor network health (ping, connection status)")
    print("   -> Pause trading when network is unstable")
    print("\n" + "="*70)


if __name__ == "__main__":
    # Run interactive demonstration
    run_all_demos()
