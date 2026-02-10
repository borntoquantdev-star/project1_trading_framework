"""
Execution Module
โมดูลสำหรับการยิงคำสั่งซื้อ/ขาย (Order Execution)
"""
import ccxt
from utils import logger, notify_buy_order, notify_sell_order, notify_error
import config

class OrderExecutor:
    """คลาสสำหรับการจัดการคำสั่งซื้อขาย"""
    
    def __init__(self, exchange):
        """
        เริ่มต้น Order Executor
        
        Args:
            exchange: CCXT Exchange object
        """
        self.exchange = exchange
        self.current_position = None  # เก็บข้อมูลออเดอร์ปัจจุบัน
        logger.info("✅ เริ่มต้น Order Executor")
    
    def check_balance(self, currency='USDT', required_amount=None):
        """
        ตรวจสอบยอดเงินว่าพอหรือไม่
        
        Args:
            currency (str): สกุลเงิน
            required_amount (float): จำนวนเงินที่ต้องการ
            
        Returns:
            bool: True ถ้าเงินพอ, False ถ้าไม่พอ
        """
        try:
            balance = self.exchange.fetch_balance()
            free_balance = balance[currency]['free']
            
            logger.info(f"💰 ยอดเงินคงเหลือ {currency}: {free_balance:.2f}")
            
            if required_amount:
                if free_balance >= required_amount:
                    logger.info(f"✅ ยอดเงินเพียงพอ (ต้องการ {required_amount:.2f})")
                    return True
                else:
                    logger.warning(f"⚠️ ยอดเงินไม่พอ (ต้องการ {required_amount:.2f}, มี {free_balance:.2f})")
                    return False
            
            return free_balance > 0
            
        except Exception as e:
            logger.error(f"❌ ไม่สามารถตรวจสอบ Balance ได้: {str(e)}")
            return False
    
    def has_open_position(self, symbol=None):
        """
        ตรวจสอบว่ามี Position เปิดอยู่หรือไม่ (Idempotency Check)
        
        Args:
            symbol (str): คู่เหรียญ
            
        Returns:
            bool: True ถ้ามี Position, False ถ้าไม่มี
        """
        # ในระบบจริง ควรเช็คจาก Exchange
        # แต่เพื่อความง่าย เราเก็บไว้ใน memory
        return self.current_position is not None
    
    def place_market_buy(self, symbol, amount_usdt):
        """
        ซื้อแบบ Market Order
        
        Args:
            symbol (str): คู่เหรียญ เช่น 'BTC/USDT'
            amount_usdt (float): จำนวนเงิน USDT ที่ต้องการซื้อ
            
        Returns:
            dict: ข้อมูล Order หรือ None ถ้าล้มเหลว
        """
        if config.DRY_RUN:
            logger.info("🧪 [DRY RUN] ไม่ได้ยิง Order จริง")
            # จำลอง Order
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            
            fake_order = {
                'id': 'DRY_RUN_' + str(int(time.time())),
                'symbol': symbol,
                'type': 'market',
                'side': 'buy',
                'price': price,
                'amount': amount_usdt / price,
                'cost': amount_usdt
            }
            
            self.current_position = fake_order
            notify_buy_order(symbol, price, amount_usdt, dry_run=True)
            return fake_order
        
        # ยิง Order จริง
        try:
            # ดึงราคาปัจจุบัน
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # คำนวณปริมาณที่จะซื้อ
            amount = amount_usdt / current_price
            
            # ยิง Market Order
            logger.info(f"🚀 กำลังยิง Market Buy Order...")
            order = self.exchange.create_market_buy_order(symbol, amount)
            
            logger.info(f"✅ ซื้อสำเร็จ: {order['id']}")
            self.current_position = order
            notify_buy_order(symbol, current_price, amount_usdt, dry_run=False)
            
            return order
            
        except ccxt.InsufficientFunds as e:
            logger.error(f"❌ เงินไม่พอ: {str(e)}")
            notify_error(f"เงินไม่พอสำหรับการซื้อ {symbol}")
            return None
        except Exception as e:
            logger.error(f"❌ ไม่สามารถยิง Order ได้: {str(e)}")
            notify_error(f"Error ในการซื้อ: {str(e)}")
            return None
    
    def place_market_sell(self, symbol, amount=None):
        """
        ขายแบบ Market Order
        
        Args:
            symbol (str): คู่เหรียญ
            amount (float): จำนวนที่จะขาย (ถ้าไม่ระบุ = ขายทั้งหมด)
            
        Returns:
            dict: ข้อมูล Order หรือ None ถ้าล้มเหลว
        """
        if not self.current_position:
            logger.warning("⚠️ ไม่มี Position ให้ขาย")
            return None
        
        # ใช้ปริมาณจาก Position ถ้าไม่ระบุ
        if amount is None:
            amount = self.current_position.get('amount', 0)
        
        if config.DRY_RUN:
            logger.info("🧪 [DRY RUN] ไม่ได้ยิง Order จริง")
            
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            buy_price = self.current_position['price']
            
            # คำนวณกำไร
            profit_pct = ((current_price - buy_price) / buy_price) * 100
            
            fake_order = {
                'id': 'DRY_RUN_SELL_' + str(int(time.time())),
                'symbol': symbol,
                'type': 'market',
                'side': 'sell',
                'price': current_price,
                'amount': amount,
                'cost': amount * current_price
            }
            
            notify_sell_order(symbol, current_price, amount * current_price, profit_pct, dry_run=True)
            self.current_position = None
            return fake_order
        
        # ยิง Order จริง
        try:
            logger.info(f"🚀 กำลังยิง Market Sell Order...")
            order = self.exchange.create_market_sell_order(symbol, amount)
            
            # คำนวณกำไร
            current_price = order['price']
            buy_price = self.current_position['price']
            profit_pct = ((current_price - buy_price) / buy_price) * 100
            
            logger.info(f"✅ ขายสำเร็จ: {order['id']} (กำไร: {profit_pct:+.2f}%)")
            notify_sell_order(symbol, current_price, amount * current_price, profit_pct, dry_run=False)
            
            self.current_position = None
            return order
            
        except Exception as e:
            logger.error(f"❌ ไม่สามารถยิง Order ได้: {str(e)}")
            notify_error(f"Error ในการขาย: {str(e)}")
            return None
    
    def place_limit_order(self, symbol, side, amount, price):
        """
        ยิง Limit Order (สำหรับ Advanced Users)
        
        Args:
            symbol (str): คู่เหรียญ
            side (str): 'buy' หรือ 'sell'
            amount (float): ปริมาณ
            price (float): ราคาที่ต้องการ
            
        Returns:
            dict: ข้อมูล Order
        """
        if config.DRY_RUN:
            logger.info(f"🧪 [DRY RUN] Limit {side.upper()} ที่ราคา ${price:.2f}")
            return None
        
        try:
            if side == 'buy':
                order = self.exchange.create_limit_buy_order(symbol, amount, price)
            else:
                order = self.exchange.create_limit_sell_order(symbol, amount, price)
            
            logger.info(f"✅ ยิง Limit Order สำเร็จ: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"❌ ไม่สามารถยิง Limit Order ได้: {str(e)}")
            return None

if __name__ == "__main__":
    # ทดสอบ Executor
    import time
    from data_handler import DataHandler
    
    print("=== Testing Order Executor ===\n")
    
    if not config.validate_config():
        print("กรุณาตั้งค่า .env ให้ถูกต้องก่อน")
        exit(1)
    
    # สร้าง Data Handler
    data_handler = DataHandler()
    
    # สร้าง Executor
    executor = OrderExecutor(data_handler.exchange)
    
    # ทดสอบเช็ค Balance
    print("1. ตรวจสอบยอดเงิน:")
    executor.check_balance('USDT', config.POSITION_SIZE_USDT)
    
    # ทดสอบ Market Buy (Dry Run)
    print("\n2. ทดสอบ Market Buy Order:")
    order = executor.place_market_buy(config.SYMBOL, config.POSITION_SIZE_USDT)
    if order:
        print(f"Order: {order}")
    
    # รอสักครู่
    time.sleep(2)
    
    # ทดสอบ Market Sell
    print("\n3. ทดสอบ Market Sell Order:")
    sell_order = executor.place_market_sell(config.SYMBOL)
    if sell_order:
        print(f"Sell Order: {sell_order}")
