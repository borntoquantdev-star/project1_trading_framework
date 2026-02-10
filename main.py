"""
Main Trading Bot
จุดเริ่มต้นการทำงานของ Trading Bot
ใช้โมเดล 4-Block System: Data Handler -> Strategy -> Execution -> Safety Net
"""
import time
from datetime import datetime
import config
from utils import logger, notify_error, setup_logger
from data_handler import DataHandler
from strategy import TradingStrategy
from execution import OrderExecutor

class TradingBot:
    """คลาสหลักของ Trading Bot"""
    
    def __init__(self):
        """เริ่มต้น Bot"""
        logger.info("=" * 50)
        logger.info("🤖 เริ่มต้น Trading Bot")
        logger.info("=" * 50)
        
        # ตรวจสอบ Config
        if not config.validate_config():
            raise ValueError("Configuration ไม่ถูกต้อง กรุณาตรวจสอบไฟล์ .env")
        
        # แสดงการตั้งค่า
        self._display_settings()
        
        # สร้าง Components (4-Block System)
        try:
            # Block 1: Data Handler (ดวงตา)
            self.data_handler = DataHandler()
            
            # Block 2: Strategy (สมอง)
            self.strategy = TradingStrategy(name="RSI + EMA Strategy")
            
            # Block 3: Execution Engine (มือ)
            self.executor = OrderExecutor(self.data_handler.exchange)
            
            logger.info("✅ เริ่มต้น Bot สำเร็จ!")
            
        except Exception as e:
            logger.error(f"❌ ไม่สามารถเริ่มต้น Bot ได้: {str(e)}")
            raise
    
    def _display_settings(self):
        """แสดงการตั้งค่าของ Bot"""
        logger.info("\n📋 การตั้งค่าปัจจุบัน:")
        logger.info(f"  Exchange: {config.EXCHANGE}")
        logger.info(f"  Symbol: {config.SYMBOL}")
        logger.info(f"  Timeframe: {config.TIMEFRAME}")
        logger.info(f"  Position Size: {config.POSITION_SIZE_USDT} USDT")
        logger.info(f"  Dry Run: {config.DRY_RUN}")
        logger.info(f"  Line Notify: {config.ENABLE_LINE_NOTIFY}")
        logger.info("")
    
    def run_once(self):
        """
        รัน Bot 1 รอบ (Main Loop Logic)
        
        Returns:
            bool: True ถ้าสำเร็จ, False ถ้าเกิดข้อผิดพลาด
        """
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"🔄 เริ่มรอบใหม่ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*50}")
            
            # ============================
            # Step 1: ดึงข้อมูลตลาด (Data Handler)
            # ============================
            logger.info("\n[Step 1] ดึงข้อมูลตลาด...")
            df = self.data_handler.fetch_ohlcv()
            
            if df is None:
                logger.warning("⚠️ ไม่สามารถดึงข้อมูลได้ จะลองใหม่ในรอบถัดไป")
                return False
            
            # ============================
            # Step 2: วิเคราะห์สัญญาณ (Strategy)
            # ============================
            logger.info("\n[Step 2] วิเคราะห์สัญญาณ...")
            signal, df_analyzed = self.strategy.run_strategy(df)
            
            logger.info(f"📊 สัญญาณ: {signal}")
            
            # ============================
            # Step 3: ตรวจสอบความปลอดภัย (Safety Check)
            # ============================
            logger.info("\n[Step 3] ตรวจสอบความปลอดภัย...")
            
            if signal == 'BUY':
                # เช็คว่ามี Position เปิดอยู่หรือยัง (Idempotency)
                if self.executor.has_open_position():
                    logger.info("⚠️ มี Position เปิดอยู่แล้ว ไม่ซื้อซ้ำ")
                    return True
                
                # เช็คยอดเงิน
                if not self.executor.check_balance('USDT', config.POSITION_SIZE_USDT):
                    logger.warning("⚠️ ยอดเงินไม่พอ ข้ามการซื้อ")
                    return True
                
                # ============================
                # Step 4: ยิงคำสั่งซื้อ (Execution)
                # ============================
                logger.info("\n[Step 4] ยิงคำสั่งซื้อ...")
                order = self.executor.place_market_buy(
                    config.SYMBOL,
                    config.POSITION_SIZE_USDT
                )
                
                if order:
                    logger.info("✅ ซื้อสำเร็จ!")
                else:
                    logger.error("❌ ซื้อไม่สำเร็จ")
            
            elif signal == 'SELL':
                # เช็คว่ามี Position ให้ขายหรือไม่
                if not self.executor.has_open_position():
                    logger.info("⚠️ ไม่มี Position ให้ขาย")
                    return True
                
                # ============================
                # Step 4: ยิงคำสั่งขาย (Execution)
                # ============================
                logger.info("\n[Step 4] ยิงคำสั่งขาย...")
                order = self.executor.place_market_sell(config.SYMBOL)
                
                if order:
                    logger.info("✅ ขายสำเร็จ!")
                else:
                    logger.error("❌ ขายไม่สำเร็จ")
            
            else:  # WAIT
                logger.info("⏳ รอสัญญาณ...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการรัน: {str(e)}")
            notify_error(f"Error ใน Main Loop: {str(e)}")
            return False
    
    def run_loop(self):
        """
        รัน Bot แบบ Loop ต่อเนื่อง
        พร้อม Error Handling และ Retry Logic
        """
        logger.info("🚀 เริ่มรัน Bot แบบต่อเนื่อง...")
        logger.info(f"⏰ Loop Interval: {config.LOOP_INTERVAL} วินาที\n")
        
        retry_count = 0
        max_retries = 5
        
        while True:
            try:
                # รัน 1 รอบ
                success = self.run_once()
                
                if success:
                    retry_count = 0  # รีเซ็ต retry counter
                else:
                    retry_count += 1
                    logger.warning(f"⚠️ รอบนี้ไม่สำเร็จ (Retry: {retry_count}/{max_retries})")
                
                # ถ้า Fail เกินจำนวนที่กำหนด
                if retry_count >= max_retries:
                    logger.error("❌ ล้มเหลวเกินจำนวนที่กำหนด หยุด Bot")
                    notify_error(f"Bot หยุดทำงานหลังจาก Retry {max_retries} ครั้ง")
                    break
                
                # รอตามที่กำหนด
                logger.info(f"\n💤 รอ {config.LOOP_INTERVAL} วินาที ก่อนรอบถัดไป...")
                time.sleep(config.LOOP_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n\n⛔ ผู้ใช้หยุดการทำงานของ Bot (Ctrl+C)")
                break
                
            except Exception as e:
                logger.error(f"❌ เกิด Error ที่ไม่คาดคิด: {str(e)}")
                notify_error(f"Critical Error: {str(e)}")
                
                # รอแล้วลองใหม่
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"รอ 10 วินาที แล้วลองใหม่... ({retry_count}/{max_retries})")
                    time.sleep(10)
                else:
                    logger.error("❌ Retry เกินจำนวนที่กำหนด หยุด Bot")
                    break
        
        logger.info("\n🛑 Bot หยุดทำงาน")

# ======================
# Entry Point
# ======================
def main():
    """ฟังก์ชันหลักสำหรับเริ่มต้น Bot"""
    try:
        # สร้าง Bot
        bot = TradingBot()
        
        # ถามผู้ใช้ว่าจะรันแบบไหน
        print("\n" + "="*50)
        print("เลือก Mode การทำงาน:")
        print("  1. รัน 1 รอบเท่านั้น (Test)")
        print("  2. รันแบบต่อเนื่อง (Production)")
        print("="*50)
        
        choice = input("เลือก (1 หรือ 2): ").strip()
        
        if choice == '1':
            logger.info("\n🧪 รัน Bot 1 รอบ (Test Mode)")
            bot.run_once()
        else:
            logger.info("\n🚀 รัน Bot แบบต่อเนื่อง (จะวนลูปไปเรื่อยๆ)")
            logger.info("⚠️ กด Ctrl+C เพื่อหยุด Bot\n")
            bot.run_loop()
        
    except Exception as e:
        logger.error(f"❌ ไม่สามารถเริ่มต้น Bot ได้: {str(e)}")
        notify_error(f"Bot Startup Failed: {str(e)}")

if __name__ == "__main__":
    main()
