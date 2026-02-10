# 🔧 Troubleshooting Guide

## ❌ Error: "Invalid Api-Key ID"

### สาเหตุ
API Key แต่ละ Exchange **ไม่สามารถใช้ข้ามกันได้**:

- API Key จาก `binance.com` → ใช้ได้แค่ **Binance Global** เท่านั้น
- API Key จาก `binance.th` → ใช้ได้แค่ **Binance TH** เท่านั้น  
- API Key จาก `testnet.binance.vision` → ใช้ได้แค่ **Binance Testnet** เท่านั้น

### แนวทางแก้ไข

#### วิธีที่ 1: ใช้ Public API (แนะนำ - ไม่ต้องมี API Key)

ถ้า**แค่ต้องการดึงข้อมูล** (ไม่เทรด) สามารถใช้ Public API โดยไม่ต้อง API Key เลย:

```python
from data_handler import DataHandler

# ใช้ Public API - ไม่ต้อง API Key
data_handler = DataHandler(use_public_only=True)

# ดึงข้อมูลได้ปกติ
df = data_handler.fetch_ohlcv('BTC/USDT', '1h', 100)
price = data_handler.get_current_price('BTC/USDT')
```

**ข้อดี:**
- ✅ ไม่ต้องสมัคร API Key
- ✅ ไม่ต้อง KYC
- ✅ ใช้ได้ทันที

**ข้อจำกัด:**
- ❌ ดึงข้อมูลได้อย่างเดียว
- ❌ เทรดไม่ได้ (ไม่สามารถยิง Order)
- ❌ เช็ค Balance ไม่ได้

#### วิธีที่ 2: ใช้ API Key ที่ถูกต้อง

##### Binance Thailand
1. ไปที่ https://www.binance.th/th/my/settings/api-management
2. สร้าง API Key ใหม่
3. ตั้งค่าใน `.env`:
   ```env
   EXCHANGE=binanceth
   API_KEY=<api_key_จาก_binance.th>
   API_SECRET=<api_secret_จาก_binance.th>
   ```

##### Binance Testnet

> [!WARNING]
> ห้ามสับสน! **demo.binance.com** (Paper Trading) ≠ **testnet.binance.vision** (API Testnet)

**ขั้นตอนที่ถูกต้อง:**
1. ไปที่ https://testnet.binance.vision/ (ไม่ใช่ demo.binance.com)
2. Login ด้วย GitHub
3. คลิก "Generate HMAC_SHA256 Key"
4. คัดลอก API Key และ Secret Key
5. ไปที่ Faucet รับเหรียญทดสอบฟรี (BTC, USDT, BNB)
6. ตั้งค่าใน `.env`:
   ```env
   EXCHANGE=binance_testnet
   USE_TESTNET=true
   API_KEY=vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A
   API_SECRET=NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j
   ```

**เช็คว่าถูกต้อง:** ถ้า API Key ขึ้นต้นด้วย `vmPUZE6mv9...` = ถูกต้อง!

---

## ❌ Error: Network Error / Timeout

### สาเหตุ
- เน็ตหลุดขณะดึงข้อมูล
- Exchange Down หรือ Maintenance
- Rate Limit (ยิง Request เยอะเกินไป)

### แนวทางแก้ไข

1. **เช็คอินเทอร์เน็ต**
   ```bash
   ping api.binance.com
   ```

2. **เพิ่ม Retry Logic** (มีอยู่แล้วใน `data_handler.py`)
   ```python
   df = data_handler.retry_on_network_error(
       lambda: data_handler.fetch_ohlcv(),
       max_retries=5,
       delay=10
   )
   ```

3. **ลด Rate** - ใส่ `time.sleep()` ระหว่างการดึงข้อมูล

---

## ❌ Error: Symbol not found

### สาเหตุ
คู่เหรียญที่เลือกไม่มีใน Exchange นั้น

### แนวทางแก้ไข

1. **เช็คว่ามี Symbol หรือไม่:**
   ```python
   markets = data_handler.exchange.load_markets()
   print('BTC/USDT' in markets)  # True/False
   ```

2. **ดูรายการ Symbol ทั้งหมด:**
   ```python
   markets = data_handler.exchange.load_markets()
   symbols = list(markets.keys())
   print(symbols[:10])  # แสดง 10 อันแรก
   ```

3. **Binance TH มี Symbol น้อยกว่า Binance Global**
   - ถ้าไม่มี Symbol ที่ต้องการ ให้ใช้ Binance Global แทน

---

## 💡 เคล็ดลับ

### ทดสอบการเชื่อมต่อ

```bash
# ทดสอบ Data Handler
python data_handler.py

# เลือก Option 1 (Public API) ถ้าไม่มี API Key
# เลือก Option 2 (Private API) ถ้ามี API Key
```

### ตรวจสอบ Config

```bash
python config.py
```

ถ้าขึ้น ✅ = Config ถูกต้อง  
ถ้าขึ้น ❌ = มีอะไรผิดพลาด แก้ไขตามที่บอก

---

## 📞 ยังแก้ไม่ได้?

1. เช็ค Log อย่างละเอียด (ไฟล์ `bot.log`)
2. ลองใช้ Binance Global ก่อน (ง่ายที่สุด)
3. ลองใช้ Testnet (ฟรี ไม่เสี่ยง)
4. ลองใช้ Public API (ไม่ต้อง API Key)

---

**อัปเดตล่าสุด:** 2026-01-08
