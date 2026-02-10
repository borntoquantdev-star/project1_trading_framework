"""
Configuration Module
โมดูลสำหรับจัดการค่าต่างๆ ของบอท
"""
import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# ======================
# Exchange Configuration
# ======================
EXCHANGE = os.getenv('EXCHANGE', 'binance')  # binance, binanceth, binance_testnet, okx, bybit
API_KEY = os.getenv('API_KEY', '')
API_SECRET = os.getenv('API_SECRET', '')

# Binance Testnet Mode
USE_TESTNET = os.getenv('USE_TESTNET', 'false').lower() == 'true'

# ======================
# Trading Configuration
# ======================
SYMBOL = 'BTC/USDT'  # คู่เหรียญที่จะเทรด
TIMEFRAME = '15m'  # ช่วงเวลาแท่งเทียน (1m, 5m, 15m, 1h, 4h, 1d)
LIMIT_CANDLES = 200  # จำนวนแท่งเทียนที่ต้องการดึง

# ======================
# Risk Management
# ======================
POSITION_SIZE_USDT = 20  # ขนาดออเดอร์ในหน่วย USDT
STOP_LOSS_PERCENT = 2.0  # Stop Loss เป็น % (ถ้าใช้)
TAKE_PROFIT_PERCENT = 5.0  # Take Profit เป็น %

# ======================
# Bot Behavior
# ======================
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'  # true = ไม่ยิง Order จริง
LOOP_INTERVAL = 60  # รอกี่วินาทีระหว่างการ Loop (สำหรับ Timeframe ใหญ่ ใช้ 60-300)

# ======================
# Line Notify
# ======================
LINE_NOTIFY_TOKEN = os.getenv('LINE_NOTIFY_TOKEN', '')
ENABLE_LINE_NOTIFY = len(LINE_NOTIFY_TOKEN) > 0

# ======================
# Validation
# ======================
def validate_config():
    """ตรวจสอบว่า Config ครบถ้วนหรือไม่"""
    errors = []
    
    if not API_KEY or API_KEY == 'your_api_key_here':
        errors.append("⚠️ API_KEY ยังไม่ได้ตั้งค่า กรุณาแก้ไขไฟล์ .env")
    
    if not API_SECRET or API_SECRET == 'your_api_secret_here':
        errors.append("⚠️ API_SECRET ยังไม่ได้ตั้งค่า กรุณาแก้ไขไฟล์ .env")
    
    if EXCHANGE not in ['binance', 'binanceth', 'binance_testnet', 'okx', 'bybit']:
        errors.append(f"⚠️ EXCHANGE ไม่ถูกต้อง: {EXCHANGE}")
    
    if EXCHANGE == 'binance_testnet' and not USE_TESTNET:
        errors.append("⚠️ ใช้ binance_testnet แต่ USE_TESTNET=false")
    
    if errors:
        print("\n❌ พบข้อผิดพลาดในการตั้งค่า:")
        for error in errors:
            print(f"  {error}")
        return False
    
    print("✅ Configuration ถูกต้องครบถ้วน")
    return True

if __name__ == "__main__":
    # ทดสอบ Config
    print("=== Trading Bot Configuration ===")
    print(f"Exchange: {EXCHANGE}")
    print(f"Testnet: {USE_TESTNET}")
    print(f"Symbol: {SYMBOL}")
    print(f"Timeframe: {TIMEFRAME}")
    print(f"Dry Run: {DRY_RUN}")
    print(f"Line Notify: {ENABLE_LINE_NOTIFY}")
    print("\nValidating...")
    validate_config()
