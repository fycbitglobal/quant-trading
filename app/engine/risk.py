import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, initial_balance: float = 1000.0):
        """
        ARES QUANT Risk Yönetim Modülü.
        Sadece parayı yönetmez, matematiksel olarak iflas riskini engeller.
        """
        self.balance = initial_balance
        
        # 🛡️ RİSK PARAMETRELERİ
        self.max_risk_per_trade = 0.01       # Her işlemde kasanın sadece %1'i riske edilir (Sıkılaştırıldı)
        self.max_position_size_pct = 0.20    # Tek bir coin, kasanın %20'sinden fazlasını kaplayamaz
        self.max_daily_loss = 0.05           # Günlük %5 zarar olursa sistem kendini kapatır (Kill Switch)
        
        self.current_daily_loss = 0.0
        self.max_open_trades = 3             # Aynı anda max 3 pozisyon

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """
        Sinyal gücü ve Stop-Loss mesafesine göre işlem miktarını hesaplar.
        Sonsuz miktar (division by zero) ve aşırı risk hatalarını engeller.
        """
        try:
            # 1. Adım: Risk tutarını belirle (Örn: 1000$ * %1 = 10$)
            risk_amount = self.balance * self.max_risk_per_trade
            
            # 2. Adım: Stop mesafesini hesapla
            price_diff = abs(entry_price - stop_loss)
            
            # 🛡️ KORUMA: Stop mesafesi çok darsa veya sıfırsa işlemi reddet
            # (Sıfır stop hatasını burada engelliyoruz)
            if price_diff < (entry_price * 0.001): 
                logger.warning("⚠️ RiskManager: Stop mesafesi çok dar, işlem reddedildi.")
                return 0.0
            
            # 3. Adım: Teorik miktar hesapla (Risk / Mesafe)
            amount = risk_amount / price_diff
            
            # 🛡️ KORUMA: Maksimum Pozisyon Limiti
            # Kasanın %20'sinden fazla tek bir coin'e bağlanmayı engelle
            max_allowed_amount = (self.balance * self.max_position_size_pct) / entry_price
            
            final_amount = min(amount, max_allowed_amount)
            return final_amount

        except Exception as e:
            logger.error(f"Risk hesaplama kritik hatası: {e}")
            return 0.0

    def check_kill_switch(self, current_loss: float) -> bool:
        """
        Günlük toplam zarar, maksimum limitleri aşmış mı kontrol eder.
        """
        self.current_daily_loss = current_loss
        
        if self.current_daily_loss >= (self.balance * self.max_daily_loss):
            logger.critical("🚨 KILL SWITCH ACTIVATED: Günlük maksimum zarar limitine ulaşıldı!")
            return True
        return False

    def update_balance(self, new_balance: float):
        """
        Sistem bakiyesini günceller (Kâr/Zarar sonrası).
        """
        self.balance = new_balance
        logger.info(f"💰 Kasa bakiyesi güncellendi: {self.balance:.2f} USDT")
