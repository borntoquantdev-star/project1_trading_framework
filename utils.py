"""
Utilities Module
โมดูลเครื่องมือเสริม: Line Notify, Logger
"""
import logging
import requests
from datetime import datetime
import config

# ======================
# Logger Setup
# ======================
def setup_logger(name='TradingBot', log_file='bot.log'):
    """สร้าง Logger สำหรับบันทึกข้อมูล"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# สร้าง Logger หลัก
logger = setup_logger()

# ======================
# Line Notify
# ======================
def send_line_notify(message):
    """
    ส่งแจ้งเตือนไปยัง Line Notify
    
    Args:
        message (str): ข้อความที่ต้องการส่ง
        
    Returns:
        bool: True ถ้าส่งสำเร็จ, False ถ้าไม่สำเร็จ
    """
    if not config.ENABLE_LINE_NOTIFY:
        logger.warning("Line Notify ไม่ได้เปิดใช้งาน (ไม่มี TOKEN)")
        return False
    
    url = 'https://notify-api.line.me/api/notify'
    headers = {
        'Authorization': f'Bearer {config.LINE_NOTIFY_TOKEN}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'message': message}
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ ส่ง Line Notify สำเร็จ")
            return True
        else:
            logger.error(f"❌ ส่ง Line Notify ไม่สำเร็จ: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Line Notify Error: {str(e)}")
        return False

# ======================
# Notification Templates
# ======================
def notify_buy_order(symbol, price, amount, dry_run=False):
    """แจ้งเตือนเมื่อมีคำสั่งซื้อ"""
    mode = "🧪 [DRY RUN]" if dry_run else "🚀 [LIVE]"
    message = f"""
{mode} BUY ORDER
━━━━━━━━━━━━━━
Symbol: {symbol}
Price: ${price:,.2f}
Amount: {amount} USDT
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """.strip()
    send_line_notify(message)
    logger.info(message)

def notify_sell_order(symbol, price, amount, profit_pct, dry_run=False):
    """แจ้งเตือนเมื่อมีคำสั่งขาย"""
    mode = "🧪 [DRY RUN]" if dry_run else "🚀 [LIVE]"
    emoji = "📈" if profit_pct > 0 else "📉"
    message = f"""
{mode} SELL ORDER {emoji}
━━━━━━━━━━━━━━
Symbol: {symbol}
Price: ${price:,.2f}
Amount: {amount} USDT
Profit: {profit_pct:+.2f}%
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """.strip()
    send_line_notify(message)
    logger.info(message)

def notify_error(error_message):
    """แจ้งเตือนเมื่อเกิด Error"""
    message = f"""
❌ BOT ERROR
━━━━━━━━━━━━━━
{error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """.strip()
    send_line_notify(message)
    logger.error(message)

def notify_daily_summary(trades_count, win_rate, total_profit_pct):
    """แจ้งเตือนสรุปรายวัน (Optional)"""
    message = f"""
📊 DAILY SUMMARY
━━━━━━━━━━━━━━
Trades: {trades_count}
Win Rate: {win_rate:.1f}%
Total Profit: {total_profit_pct:+.2f}%
Date: {datetime.now().strftime('%Y-%m-%d')}
    """.strip()
    send_line_notify(message)
    logger.info(message)

# ======================
# Helper Functions
# ======================
def format_number(num, decimals=2):
    """จัดรูปแบบตัวเลขให้อ่านง่าย"""
    return f"{num:,.{decimals}f}"

def calculate_percentage_change(old_value, new_value):
    """คำนวณเปอร์เซ็นต์การเปลี่ยนแปลง"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100

if __name__ == "__main__":
    # ทดสอบ Utilities
    logger.info("Testing Logger...")
    
    # ทดสอบ Line Notify (ถ้ามี Token)
    if config.ENABLE_LINE_NOTIFY:
        send_line_notify("🧪 Testing from Trading Bot")
        notify_buy_order("BTC/USDT", 50000, 20, dry_run=True)
    else:
        print("⚠️ Line Notify ไม่ได้เปิดใช้งาน")
