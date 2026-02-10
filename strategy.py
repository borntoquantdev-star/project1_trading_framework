"""
Strategy Module
โมดูลสำหรับ Logic การเทรด (Setup-Trigger-Filter Model)
"""
import pandas as pd
from utils import logger

class TradingStrategy:
    """
    คลาสกลยุทธ์การเทรด
    ใช้โมเดล Setup-Trigger-Filter
    """
    
    def __init__(self, name="Default Strategy"):
        """เริ่มต้นกลยุทธ์"""
        self.name = name
        logger.info(f"📊 เริ่มต้นกลยุทธ์: {self.name}")
    
    def calculate_indicators(self, df):
        """
        คำนวณ Indicators ต่างๆ
        
        Args:
            df (pd.DataFrame): ข้อมูล OHLCV
            
        Returns:
            pd.DataFrame: ข้อมูลที่เพิ่ม Indicators แล้ว
        """
        # สำเนาข้อมูลเพื่อไม่ให้กระทบต้นฉบับ
        df = df.copy()
        
        # คำนวณ EMA (Exponential Moving Average)
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # คำนวณ RSI (Relative Strength Index)
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        
        # คำนวณ Volume Average
        df['volume_avg'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def _calculate_rsi(self, prices, period=14):
        """
        คำนวณ RSI
        
        Args:
            prices (pd.Series): ราคา Close
            period (int): ช่วงเวลา RSI
            
        Returns:
            pd.Series: ค่า RSI
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_signal(self, df):
        """
        ตรวจสอบสัญญาณซื้อ/ขาย ตามโมเดล Setup-Trigger-Filter
        
        Args:
            df (pd.DataFrame): ข้อมูลที่คำนวณ Indicators แล้ว
            
        Returns:
            str: 'BUY', 'SELL', 'WAIT'
        """
        if df is None or len(df) < 200:
            logger.warning("⚠️ ข้อมูลไม่เพียงพอสำหรับการวิเคราะห์")
            return 'WAIT'
        
        # ดึงข้อมูลแท่งล่าสุด
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # ======================
        # SETUP: เงื่อนไขภาพใหญ่
        # ======================
        # ราคาต้องอยู่เหนือ EMA 200 (เทรนด์ขาขึ้น)
        setup_long = current['close'] > current['ema_200']
        
        # ======================
        # FILTER: ตัวกรอง
        # ======================
        # Volume ต้องมากกว่าค่าเฉลี่ย
        filter_volume = current['volume'] > current['volume_avg']
        
        # ======================
        # TRIGGER: จังหวะเข้า
        # ======================
        # BUY Signal: RSI ตัดขึ้นมาจากแดนขาย (30)
        trigger_buy = (previous['rsi'] < 30 and current['rsi'] > 30)
        
        # SELL Signal: RSI ตัดลงจากแดนซื้อ (70)
        trigger_sell = (previous['rsi'] > 70 and current['rsi'] < 70)
        
        # ======================
        # Logic การตัดสินใจ
        # ======================
        if setup_long and filter_volume and trigger_buy:
            logger.info("🟢 BUY SIGNAL ตรวจพบ!")
            logger.info(f"  → Price: ${current['close']:.2f}")
            logger.info(f"  → RSI: {current['rsi']:.2f}")
            logger.info(f"  → Volume: {current['volume']:,.0f}")
            return 'BUY'
        
        elif trigger_sell:
            logger.info("🔴 SELL SIGNAL ตรวจพบ!")
            logger.info(f"  → Price: ${current['close']:.2f}")
            logger.info(f"  → RSI: {current['rsi']:.2f}")
            return 'SELL'
        
        else:
            return 'WAIT'
    
    def run_strategy(self, df):
        """
        รัน Strategy แบบครบวงจร
        
        Args:
            df (pd.DataFrame): ข้อมูล OHLCV ดิบ
            
        Returns:
            tuple: (signal, analyzed_df)
        """
        # คำนวณ Indicators
        df_analyzed = self.calculate_indicators(df)
        
        # ตรวจสอบสัญญาณ
        signal = self.check_signal(df_analyzed)
        
        return signal, df_analyzed

# ======================
# Strategy Example 2: EMA Crossover (ตัวอย่างเพิ่มเติม)
# ======================
class EMACrossoverStrategy(TradingStrategy):
    """กลยุทธ์ EMA Crossover"""
    
    def __init__(self):
        super().__init__(name="EMA Crossover Strategy")
    
    def check_signal(self, df):
        """ตรวจสอบสัญญาณแบบ EMA Crossover"""
        if df is None or len(df) < 50:
            return 'WAIT'
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Golden Cross (EMA 20 ตัดขึ้น EMA 50)
        if previous['ema_20'] <= previous['ema_50'] and current['ema_20'] > current['ema_50']:
            logger.info("🟢 GOLDEN CROSS ตรวจพบ!")
            return 'BUY'
        
        # Death Cross (EMA 20 ตัดลง EMA 50)
        elif previous['ema_20'] >= previous['ema_50'] and current['ema_20'] < current['ema_50']:
            logger.info("🔴 DEATH CROSS ตรวจพบ!")
            return 'SELL'
        
        return 'WAIT'

if __name__ == "__main__":
    # ทดสอบ Strategy
    print("=== Testing Trading Strategy ===\n")
    
    # สร้างข้อมูลตัวอย่าง
    import numpy as np
    dates = pd.date_range(start='2024-01-01', periods=300, freq='1h')
    
    # สร้างข้อมูลจำลอง
    np.random.seed(42)
    close_prices = 50000 + np.cumsum(np.random.randn(300) * 100)
    
    df_test = pd.DataFrame({
        'open': close_prices + np.random.randn(300) * 50,
        'high': close_prices + np.abs(np.random.randn(300) * 100),
        'low': close_prices - np.abs(np.random.randn(300) * 100),
        'close': close_prices,
        'volume': np.random.randint(100, 1000, 300)
    }, index=dates)
    
    # ทดสอบกลยุทธ์ RSI
    print("1. ทดสอบ RSI Strategy:")
    strategy = TradingStrategy()
    signal, df_analyzed = strategy.run_strategy(df_test)
    print(f"Signal: {signal}\n")
    
    # ทดสอบกลยุทธ์ EMA Crossover
    print("2. ทดสอบ EMA Crossover Strategy:")
    ema_strategy = EMACrossoverStrategy()
    signal2, df_analyzed2 = ema_strategy.run_strategy(df_test)
    print(f"Signal: {signal2}")
    
    # แสดงข้อมูลล่าสุด
    print("\nข้อมูล Indicators ล่าสุด:")
    print(df_analyzed[['close', 'ema_20', 'ema_50', 'rsi', 'volume_avg']].tail())
