"""
Data Handler Module
โมดูลสำหรับดึงข้อมูลจาก Exchange ผ่าน REST API
"""
import ccxt
import pandas as pd
import time
from utils import logger
import config

class DataHandler:
    """คลาสสำหรับจัดการข้อมูลตลาด"""
    
    def __init__(self, use_public_only=False):
        """
        เริ่มต้น Exchange Connection
        
        Args:
            use_public_only (bool): ใช้แค่ Public API (ไม่ต้อง API Key) สำหรับดึงข้อมูลอย่างเดียว
        """
        try:
            # จัดการ Exchange แบบพิเศษ
            exchange_name = config.EXCHANGE
            self.use_public_only = use_public_only
            
            # ถ้าใช้ Public API อย่างเดียว ไม่ต้องใส่ API Key
            if use_public_only:
                api_key = None
                api_secret = None
                logger.info("📖 ใช้ Public API (ไม่ต้องมี API Key)")
            else:
                api_key = config.API_KEY
                api_secret = config.API_SECRET
            
            # Binance TH - ใช้ Binance Global API แทน (เพราะ CCXT ไม่รองรับ TH โดยตรง)
            if exchange_name == 'binanceth':
                logger.warning("⚠️ CCXT ไม่รองรับ Binance TH API โดยตรง")
                logger.warning("💡 แนะนำ: ใช้ EXCHANGE=binance (Binance Global) แทน")
                logger.warning("   - สามารถดึงข้อมูลได้เหมือนกัน (ราคาเดียวกัน)")
                logger.warning("   - แต่ถ้าจะเทรดต้องใช้ Binance Global Account")
                
                # ใช้ Binance Global API แทน
                exchange_class = getattr(ccxt, 'binance')
                exchange_config = {
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                    }
                }
                logger.info("🔄 เปลี่ยนไปใช้ Binance Global API...")
            
            # Binance Testnet
            elif exchange_name == 'binance_testnet' or (exchange_name == 'binance' and config.USE_TESTNET):
                exchange_class = getattr(ccxt, 'binance')
                exchange_config = {
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                    }
                }
                # ตั้งค่า Testnet URLs
                exchange_config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
                logger.info("🧪 กำลังเชื่อมต่อ Binance Testnet...")
                if not use_public_only:
                    logger.warning("⚠️ ต้องใช้ API Key จาก testnet.binance.vision เท่านั้น!")
            
            # Exchange อื่นๆ (binance, okx, bybit)
            else:
                exchange_class = getattr(ccxt, exchange_name)
                exchange_config = {
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                    }
                }
            
            # สร้าง Exchange object
            self.exchange = exchange_class(exchange_config)
            
            logger.info(f"✅ เชื่อมต่อ {config.EXCHANGE.upper()} สำเร็จ")
            
        except Exception as e:
            logger.error(f"❌ ไม่สามารถเชื่อมต่อ Exchange: {str(e)}")
            raise
    
    def fetch_ohlcv(self, symbol=None, timeframe=None, limit=None):
        """
        ดึงข้อมูล OHLCV (Open, High, Low, Close, Volume)
        
        Args:
            symbol (str): คู่เหรียญ เช่น 'BTC/USDT'
            timeframe (str): ช่วงเวลา เช่น '15m', '1h'
            limit (int): จำนวนแท่งเทียน
            
        Returns:
            pd.DataFrame: ข้อมูลในรูปแบบ DataFrame
        """
        symbol = symbol or config.SYMBOL
        timeframe = timeframe or config.TIMEFRAME
        limit = limit or config.LIMIT_CANDLES
        
        try:
            # ดึงข้อมูล OHLCV
            logger.info(f"กำลังดึงข้อมูล {symbol} ({timeframe})...")
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # แปลงเป็น DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # แปลง timestamp เป็น datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"✅ ดึงข้อมูลสำเร็จ {len(df)} แท่งเทียน")
            return df
            
        except ccxt.NetworkError as e:
            logger.error(f"❌ Network Error: {str(e)}")
            return None
        except ccxt.AuthenticationError as e:
            logger.error(f"❌ Authentication Error: {str(e)}")
            logger.error("💡 แนวทางแก้ไข:")
            if config.EXCHANGE == 'binanceth':
                logger.error("   - ต้องใช้ API Key จาก https://www.binance.th/ เท่านั้น")
            elif config.EXCHANGE == 'binance_testnet':
                logger.error("   - ต้องใช้ API Key จาก https://testnet.binance.vision/ เท่านั้น")
            logger.error("   - หรือใช้ Public API (ไม่ต้อง API Key) โดยสร้าง DataHandler(use_public_only=True)")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"❌ Exchange Error: {str(e)}")
            if "Invalid Api-Key" in str(e):
                logger.error("💡 API Key ไม่ถูกต้องหรือไม่ตรงกับ Exchange")
                logger.error("   - Binance Global: ใช้ API Key จาก binance.com")
                logger.error("   - Binance TH: ใช้ API Key จาก binance.th")
                logger.error("   - Binance Testnet: ใช้ API Key จาก testnet.binance.vision")
            return None
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            return None
    
    def get_current_price(self, symbol=None):
        """
        ดึงราคาปัจจุบัน
        
        Args:
            symbol (str): คู่เหรียญ
            
        Returns:
            float: ราคาปัจจุบัน
        """
        symbol = symbol or config.SYMBOL
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.info(f"💰 ราคาปัจจุบัน {symbol}: ${price:,.2f}")
            return price
            
        except Exception as e:
            logger.error(f"❌ ไม่สามารถดึงราคาได้: {str(e)}")
            return None
    
    def get_balance(self, currency='USDT'):
        """
        ตรวจสอบยอดเงิน
        
        Args:
            currency (str): สกุลเงินที่ต้องการเช็ค เช่น 'USDT'
            
        Returns:
            dict: {'free': xxx, 'used': xxx, 'total': xxx}
        """
        try:
            balance = self.exchange.fetch_balance()
            
            if currency in balance:
                return {
                    'free': balance[currency]['free'],
                    'used': balance[currency]['used'],
                    'total': balance[currency]['total']
                }
            else:
                logger.warning(f"⚠️ ไม่พบสกุล {currency}")
                return None
                
        except Exception as e:
            logger.error(f"❌ ไม่สามารถดึง Balance ได้: {str(e)}")
            return None
    
    def retry_on_network_error(self, func, max_retries=3, delay=10):
        """
        Retry Logic สำหรับ Network Error
        
        Args:
            func (callable): ฟังก์ชันที่ต้องการ retry
            max_retries (int): จำนวนครั้งที่ลองใหม่
            delay (int): เวลารอระหว่าง retry (วินาที)
            
        Returns:
            ผลลัพธ์จากฟังก์ชัน หรือ None ถ้าล้มเหลว
        """
        for attempt in range(max_retries):
            try:
                return func()
            except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Network Error (ลองครั้งที่ {attempt + 1}/{max_retries})")
                    logger.warning(f"รอ {delay} วินาทีแล้วลองใหม่...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ ล้มเหลวหลังจากลอง {max_retries} ครั้ง")
                    return None
        return None

if __name__ == "__main__":
    # ทดสอบ Data Handler
    print("=== Testing Data Handler ===\n")
    
    print("เลือกโหมดการทดสอบ:")
    print("1. Public API (ไม่ต้อง API Key - แนะนำสำหรับ Testnet/TH)")
    print("2. Private API (ต้องมี API Key)")
    choice = input("เลือก (1 หรือ 2): ").strip()
    
    use_public = (choice == '1')
    
    if use_public:
        print("\n📖 ใช้ Public API - ไม่ต้อง API Key")
        print("   (สามารถดึงข้อมูลได้ แต่ไม่สามารถเทรดได้)\n")
        data_handler = DataHandler(use_public_only=True)
    else:
        if not config.validate_config():
            print("กรุณาตั้งค่า .env ให้ถูกต้องก่อน")
            exit(1)
        data_handler = DataHandler(use_public_only=False)
    
    # ทดสอบดึงข้อมูล OHLCV
    print("\n1. ทดสอบดึงข้อมูล OHLCV:")
    df = data_handler.fetch_ohlcv()
    if df is not None:
        print(df.tail())
        print("\n✅ ดึงข้อมูลสำเร็จ!")
    
    # ทดสอบดึงราคาปัจจุบัน
    print("\n2. ทดสอบดึงราคาปัจจุบัน:")
    price = data_handler.get_current_price()
    
    if not use_public:
        # ทดสอบดึง Balance (ต้องมี API Key)
        print("\n3. ทดสอบดึง Balance:")
        balance = data_handler.get_balance()
        if balance:
            print(f"USDT Balance: {balance}")
    else:
        print("\n💡 ข้าม Balance Check เพราะใช้ Public API")
