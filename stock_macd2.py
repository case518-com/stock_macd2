"""
台股月MACD第一根紅K掃描器 - 完整版（所有上市櫃股票）
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import requests
from io import StringIO
warnings.filterwarnings('ignore')

# 設定頁面
st.set_page_config(
    page_title="台股月MACD掃描器（完整版）",
    page_icon="🔍",
    layout="wide"
)

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft JhengHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class StockListFetcher:
    """抓取完整台股清單"""
    
    @staticmethod
    def fetch_twse_stocks():
        """抓取上市股票清單，回傳 {代號.TW: 中文名稱} 的 dict"""
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        try:
            url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
            # 關閉 SSL 驗證，加上 headers，增加重試次數
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            response.encoding = 'big5'
            
            tables = pd.read_html(StringIO(response.text))
            df = tables[0]
            df = df[df[0].str.contains('　', na=False)]
            df[['stock_code', 'stock_name']] = df[0].str.split('　', n=1, expand=True)
            df = df[df['stock_code'].str.match(r'^\d{4}$', na=False)]
            df['stock_name'] = df['stock_name'].str.strip()
            
            stock_dict = {f"{r['stock_code']}.TW": r['stock_name'] for _, r in df.iterrows()}
            
            if len(stock_dict) < 100:  # 如果資料太少，可能有問題
                st.warning(f"⚠️ 上市股票數量異常: {len(stock_dict)} 檔")
            
            return stock_dict
            
        except Exception as e:
            st.error(f"❌ 抓取上市股票失敗: {str(e)[:200]}")
            st.info("💡 將使用快速模式的預設清單")
            return {}
    
    @staticmethod
    def fetch_tpex_stocks():
        """抓取上櫃股票清單，回傳 {代號.TWO: 中文名稱} 的 dict"""
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        try:
            url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=4'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            response.encoding = 'big5'
            
            tables = pd.read_html(StringIO(response.text))
            df = tables[0]
            df = df[df[0].str.contains('　', na=False)]
            df[['stock_code', 'stock_name']] = df[0].str.split('　', n=1, expand=True)
            df = df[df['stock_code'].str.match(r'^\d{4}$', na=False)]
            df['stock_name'] = df['stock_name'].str.strip()
            
            stock_dict = {f"{r['stock_code']}.TWO": r['stock_name'] for _, r in df.iterrows()}
            
            if len(stock_dict) < 50:
                st.warning(f"⚠️ 上櫃股票數量異常: {len(stock_dict)} 檔")
            
            return stock_dict
            
        except Exception as e:
            st.error(f"❌ 抓取上櫃股票失敗: {str(e)[:200]}")
            st.info("💡 將使用快速模式的預設清單")
            return {}
    
    @staticmethod
    def get_all_tw_stocks():
        """取得所有上市櫃股票，回傳 {代號: 中文名稱} 的 dict"""
        st.info("🔄 正在從證交所抓取最新股票清單...")
        
        twse_dict = StockListFetcher.fetch_twse_stocks()
        tpex_dict = StockListFetcher.fetch_tpex_stocks()
        
        # 如果都抓取失敗，回退到快速模式
        if not twse_dict and not tpex_dict:
            st.warning("⚠️ 無法連線至證交所網站，將使用快速模式預設清單")
            return StockListFetcher.get_preset_stocks()
        
        all_dict = {**twse_dict, **tpex_dict}
        
        if twse_dict:
            st.success(f"✓ 成功抓取 {len(twse_dict)} 檔上市股票")
        if tpex_dict:
            st.success(f"✓ 成功抓取 {len(tpex_dict)} 檔上櫃股票")
        st.success(f"✓ 總計 {len(all_dict)} 檔股票")
        
        return all_dict
    
    @staticmethod
    def get_preset_stocks():
        """預設股票清單（快速測試用）"""
        # 主要上市股票
        market_cap_large = [
            '2330.TW', '2454.TW', '2317.TW', '6505.TW', '2308.TW',
            '2882.TW', '2881.TW', '2303.TW', '2412.TW', '2886.TW',
            '2382.TW', '2891.TW', '3711.TW', '2002.TW', '1301.TW',
            '1303.TW', '2912.TW', '2884.TW', '1326.TW', '2357.TW',
        ]
        
        electronics = [
            '2409.TW', '3034.TW', '2327.TW', '3037.TW', '2379.TW',
            '3045.TW', '2395.TW', '2377.TW', '2353.TW', '4938.TW',
            '6669.TW', '3443.TW', '6415.TW', '5274.TW', '6789.TW',
        ]
        
        shipping = ['2603.TW', '2609.TW', '2615.TW', '2618.TW', '5608.TW']
        
        finance = [
            '2880.TW', '2885.TW', '2887.TW', '2890.TW', '2892.TW',
            '5880.TW', '2801.TW', '2834.TW', '2836.TW', '2809.TW',
        ]
        
        traditional = [
            '1216.TW', '1402.TW', '2207.TW', '2301.TW', '2474.TW',
            '4904.TW', '9904.TW', '1101.TW', '2105.TW', '2049.TW',
        ]
        
        all_stocks = list(set(
            market_cap_large + electronics + shipping + finance + traditional
        ))
        # 預設清單沒有中文名稱，回傳 dict（名稱先填空，之後掃描時再補）
        return {code: '' for code in sorted(all_stocks)}


class StockScanner:
    """股票掃描器"""
    
    @staticmethod
    def fetch_monthly_data(stock_code, period='2y'):
        """抓取月線數據"""
        try:
            ticker = yf.Ticker(stock_code)
            data = ticker.history(period=period, interval='1mo')
            
            if data.empty or len(data) < 12:
                return None
            
            return data
            
        except Exception as e:
            return None
    
    @staticmethod
    def calculate_monthly_macd(data, fast=12, slow=26, signal=9):
        """計算月線MACD"""
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        data['MACD'] = macd
        data['MACD_Signal'] = signal_line
        data['MACD_Histogram'] = histogram
        
        return data
    
    @staticmethod
    def calculate_monthly_kd(data, period=9, k_period=3, d_period=3):
        """計算月線KD"""
        low_min = data['Low'].rolling(window=period).min()
        high_max = data['High'].rolling(window=period).max()
        rsv = 100 * (data['Close'] - low_min) / (high_max - low_min)
        k = rsv.ewm(span=k_period, adjust=False).mean()
        d = k.ewm(span=d_period, adjust=False).mean()
        
        data['K'] = k
        data['D'] = d
        
        return data
    
    @staticmethod
    def calculate_monthly_rsi(data, period=14):
        """計算月線RSI"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        data['RSI'] = rsi
        return data
    
    @staticmethod
    def get_dividend_info(stock_code):
        """取得股利資訊"""
        try:
            ticker = yf.Ticker(stock_code)
            dividends = ticker.dividends
            
            if dividends is None or len(dividends) == 0:
                return {'有發股利': False, '近年股利': 0, '殖利率': 0}
            
            # 修正1：去除重複索引（yfinance 有時會重複紀錄同一筆股利）
            dividends = dividends[~dividends.index.duplicated(keep='last')]
            
            # 修正2：用明確的 UTC 時間戳篩選近一年，避免 .last() 時區問題
            one_year_ago = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=365)
            recent_dividends = dividends[dividends.index >= one_year_ago]
            recent_div = recent_dividends.sum()
            
            # 取得當前股價計算殖利率
            try:
                hist = ticker.history(period='5d')
                if hist.empty:
                    return {'有發股利': False, '近年股利': 0, '殖利率': 0}
                current_price = hist['Close'].iloc[-1]
                dividend_yield = (recent_div / current_price * 100) if current_price > 0 else 0
            except:
                dividend_yield = 0
            
            # 修正3：殖利率合理性過濾（台股正常範圍約 0~15%，超過 20% 視為資料異常）
            if dividend_yield > 20:
                dividend_yield = 0
            
            return {
                '有發股利': recent_div > 0,
                '近年股利': round(recent_div, 2),
                '殖利率': round(dividend_yield, 2)
            }
        except:
            return {'有發股利': False, '近年股利': 0, '殖利率': 0}
    
    @staticmethod
    def check_first_macd_red(data):
        """檢查是否為月MACD第一根紅K"""
        if len(data) < 2:
            return False, None
        
        current_macd = data['MACD'].iloc[-1]
        current_signal = data['MACD_Signal'].iloc[-1]
        prev_macd = data['MACD'].iloc[-2]
        prev_signal = data['MACD_Signal'].iloc[-2]
        
        is_first_red = (current_macd > current_signal) and (prev_macd <= prev_signal)
        
        if not is_first_red:
            return False, None
        
        info = {
            '月MACD': round(current_macd, 4),
            '月Signal': round(current_signal, 4),
            '前期MACD': round(prev_macd, 4),
            '前期Signal': round(prev_signal, 4),
            '交叉力道': round(current_macd - current_signal, 4),
            'MACD位階': '多頭' if current_macd > 0 else '空頭',
        }
        
        confirmations = []
        
        if current_macd > 0:
            confirmations.append('MACD>0')
        
        if 'K' in data.columns and 'D' in data.columns:
            k = data['K'].iloc[-1]
            d = data['D'].iloc[-1]
            info['月K值'] = round(k, 2)
            info['月D值'] = round(d, 2)
            if k > d:
                confirmations.append('KD金叉')
            if k < 30:
                confirmations.append('K值低檔')
        
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            info['月RSI'] = round(rsi, 2)
            if rsi < 50:
                confirmations.append('RSI偏低')
        
        histogram = data['MACD_Histogram'].iloc[-1]
        if histogram > 0:
            confirmations.append('柱狀體轉正')
        
        info['確認訊號'] = ', '.join(confirmations) if confirmations else '僅MACD金叉'
        info['訊號強度'] = len(confirmations)
        
        return True, info


def scan_all_stocks(stock_dict, progress_bar, status_text, result_container):
    """掃描所有股票（即時顯示結果），stock_dict = {代號: 中文名稱}"""
    results = []
    stock_list = list(stock_dict.keys())
    total = len(stock_list)
    found_count = 0

    for idx, stock_code in enumerate(stock_list, 1):
        # 更新進度
        progress = idx / total
        progress_bar.progress(progress)
        # 從 dict 直接取中文名稱顯示在進度列
        cn_name = stock_dict.get(stock_code, '')
        status_text.text(f'掃描進度: {idx}/{total} ({progress*100:.1f}%)  {stock_code} {cn_name}  ｜  已找到 {found_count} 檔')

        # 抓取月線數據
        data = StockScanner.fetch_monthly_data(stock_code)
        if data is None:
            continue

        # 計算技術指標
        data = StockScanner.calculate_monthly_macd(data)
        data = StockScanner.calculate_monthly_kd(data)
        data = StockScanner.calculate_monthly_rsi(data)

        # 檢查訊號
        is_signal, info = StockScanner.check_first_macd_red(data)

        if is_signal:
            # ✅ 直接用證交所抓來的中文名稱
            stock_name = stock_dict.get(stock_code, stock_code)
            industry = 'N/A'
            
            # 抓取股利資訊
            dividend_info = StockScanner.get_dividend_info(stock_code)

            result = {
                '股票代號': stock_code.replace('.TW', '').replace('.TWO', ''),
                '股票名稱': stock_name,
                '市場': '上市' if stock_code.endswith('.TW') else '上櫃',
                '現價': round(data['Close'].iloc[-1], 2),
                '產業': industry,
                '有發股利': '✓' if dividend_info['有發股利'] else '✗',
                '近年股利': dividend_info['近年股利'],
                '殖利率': dividend_info['殖利率'],
            }
            result.update(info)
            results.append(result)
            found_count += 1

            # 即時顯示（中文名稱、股價、股利、MACD位階、訊號強度）
            strength = result['訊號強度']
            icon = '💎' if strength >= 4 else '🚀' if strength == 3 else '🔥' if strength == 2 else '⚡' if strength == 1 else '💡'
            macd_tag = '📈多頭' if result['MACD位階'] == '多頭' else '📉空頭'
            div_icon = '💰' if result['有發股利'] == '✓' else '🚫'
            div_text = f"殖利率 {result['殖利率']:.1f}%" if result['殖利率'] > 0 else "無股利"
            
            with result_container:
                st.success(
                    f"{icon} #{found_count}　"
                    f"**{result['股票代號']}**　{stock_name}　｜　"
                    f"💵 ${result['現價']:.2f}　｜　"
                    f"{div_icon} {div_text}　｜　"
                    f"{macd_tag}　｜　"
                    f"訊號強度: {'★' * strength}{'☆' * (4 - strength)} ({strength})"
                )

    return results


def plot_monthly_chart(data, stock_code, stock_name):
    """繪製月線圖表"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
    
    # 子圖1：月K線圖
    ax1.plot(data.index, data['Close'], label='月收盤價', linewidth=2, color='black')
    ax1.scatter(data.index[-1], data['Close'].iloc[-1], 
                color='red', s=200, zorder=5, label='當前月份')
    ax1.set_title(f'{stock_name} ({stock_code}) - 月K線圖')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('價格 (元)')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # 子圖2：月MACD
    ax2.plot(data.index, data['MACD'], label='MACD', linewidth=2, color='blue')
    ax2.plot(data.index, data['MACD_Signal'], label='Signal', linewidth=2, color='red')
    ax2.bar(data.index, data['MACD_Histogram'], label='Histogram', 
            color=['green' if x > 0 else 'red' for x in data['MACD_Histogram']], 
            alpha=0.5)
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax2.scatter(data.index[-1], data['MACD'].iloc[-1], 
                color='red', s=200, zorder=5, label='第一根紅K')
    ax2.set_title('月MACD指標（第一根紅K）')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('MACD')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # 子圖3：月KD指標
    ax3.plot(data.index, data['K'], label='K', linewidth=2, color='blue')
    ax3.plot(data.index, data['D'], label='D', linewidth=2, color='red')
    ax3.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='超買(80)')
    ax3.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='超賣(20)')
    ax3.fill_between(data.index, 0, 20, color='green', alpha=0.1)
    ax3.fill_between(data.index, 80, 100, color='red', alpha=0.1)
    ax3.set_title('月KD指標')
    ax3.set_xlabel('日期')
    ax3.set_ylabel('KD值')
    ax3.set_ylim([0, 100])
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    
    # 子圖4：月RSI指標
    ax4.plot(data.index, data['RSI'], label='RSI', linewidth=2, color='purple')
    ax4.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='超買(70)')
    ax4.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='超賣(30)')
    ax4.fill_between(data.index, 0, 30, color='green', alpha=0.1)
    ax4.fill_between(data.index, 70, 100, color='red', alpha=0.1)
    ax4.set_title('月RSI指標')
    ax4.set_xlabel('日期')
    ax4.set_ylabel('RSI值')
    ax4.set_ylim([0, 100])
    ax4.legend(loc='best')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def main():
    st.title("🔍 台股月MACD第一根紅K掃描器（完整版）")
    st.markdown("✨ 支援掃描所有上市櫃股票（約1900檔）")
    st.markdown("---")
    
    # 側邊欄設定
    with st.sidebar:
        st.header("⚙️ 掃描設定")
        
        # 選擇掃描範圍
        st.subheader("📊 掃描範圍")
        scan_mode = st.radio(
            "選擇掃描模式",
            ["🚀 快速模式（約70檔精選股）", "🔍 完整模式（全部上市櫃）"],
            help="快速模式：3-5分鐘 | 完整模式：30-60分鐘"
        )
        
        st.markdown("---")
        
        # 篩選條件
        st.subheader("🎯 進階篩選")
        
        filter_macd_positive = st.checkbox(
            "只顯示MACD>0（多頭）", 
            value=True,
            help="只保留MACD在0軸上方的標的"
        )
        
        filter_kd_low = st.checkbox(
            "只顯示K值<50", 
            value=False,
            help="只保留K值在中低檔的標的"
        )
        
        filter_rsi_low = st.checkbox(
            "只顯示RSI<60", 
            value=False,
            help="只保留RSI偏低的標的"
        )
        
        filter_has_dividend = st.checkbox(
            "只顯示有發股利", 
            value=False,
            help="只保留近一年有發放股利的標的"
        )
        
        min_dividend_yield = st.number_input(
            "最低殖利率 (%)",
            min_value=0.0,
            max_value=20.0,
            value=0.0,
            step=0.5,
            help="設定0表示不限制殖利率"
        )
        
        min_signal_strength = st.slider(
            "最低訊號強度",
            min_value=0,
            max_value=4,
            value=0,
            help="0=僅MACD金叉, 1+=額外確認"
        )
        
        st.markdown("---")
        
        if "🚀 快速模式" in scan_mode:
            st.info("💡 快速模式：掃描約70檔精選股票，約需3-5分鐘")
        else:
            st.warning("⚠️ 完整模式：掃描全部上市櫃，約需30-60分鐘！")
        
        # 開始掃描按鈕
        start_scan = st.button("🚀 開始掃描", type="primary", use_container_width=True)
    
    # 主要內容區
    if start_scan:
        # 取得股票清單（dict 格式：{代號: 中文名稱}）
        if "🚀 快速模式" in scan_mode:
            stock_dict = StockListFetcher.get_preset_stocks()
            st.info(f"📋 快速模式：準備掃描 {len(stock_dict)} 檔精選股票")
        else:
            stock_dict = StockListFetcher.get_all_tw_stocks()
            st.info(f"📋 完整模式：準備掃描 {len(stock_dict)} 檔上市櫃股票")

        if not stock_dict:
            st.error("❌ 無法取得股票清單，請檢查網路連線")
            return
        
        # 進度條
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 即時結果顯示區
        st.markdown("### 🔍 掃描中...（即時結果）")
        result_container = st.container()
        
        # 執行掃描
        start_time = datetime.now()
        results = scan_all_stocks(stock_dict, progress_bar, status_text, result_container)
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        # 清除進度顯示
        progress_bar.empty()
        status_text.empty()
        
        if not results:
            st.warning("⚠️ 目前沒有找到符合條件的股票")
            st.info(f"⏱️ 掃描完成，耗時 {elapsed_time:.1f} 秒")
            return
        
        # 轉換為DataFrame
        df = pd.DataFrame(results)
        
        # 套用篩選條件
        original_count = len(df)
        
        if filter_macd_positive:
            df = df[df['MACD位階'] == '多頭']
        
        if filter_kd_low and '月K值' in df.columns:
            df = df[df['月K值'] < 50]
        
        if filter_rsi_low and '月RSI' in df.columns:
            df = df[df['月RSI'] < 60]
        
        if filter_has_dividend:
            df = df[df['有發股利'] == '✓']
        
        if min_dividend_yield > 0:
            df = df[df['殖利率'] >= min_dividend_yield]
        
        if min_signal_strength > 0:
            df = df[df['訊號強度'] >= min_signal_strength]
        
        filtered_count = len(df)
        
        # 依訊號強度和交叉力道排序
        df = df.sort_values(['訊號強度', '交叉力道'], ascending=[False, False])
        
        st.success(f"✅ 掃描完成！找到 {original_count} 檔，篩選後剩 {filtered_count} 檔")
        st.info(f"⏱️ 耗時 {elapsed_time:.1f} 秒 ({elapsed_time/60:.1f} 分鐘)")
        
        # 顯示統計摘要
        st.markdown("---")
        st.markdown("### 📊 掃描結果統計")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("掃描股票", f"{len(stock_dict)} 檔")
        
        with col2:
            st.metric("找到股票", f"{original_count} 檔")
        
        with col3:
            st.metric("篩選後", f"{filtered_count} 檔")
        
        with col4:
            strong_signals = len(df[df['訊號強度'] >= 2])
            st.metric("強勢訊號", f"{strong_signals} 檔")
        
        with col5:
            macd_positive = len(df[df['MACD位階'] == '多頭'])
            st.metric("MACD多頭", f"{macd_positive} 檔")
        
        # 市場分布
        if '市場' in df.columns:
            st.markdown("#### 📈 市場分布")
            col1, col2 = st.columns(2)
            with col1:
                twse_count = len(df[df['市場'] == '上市'])
                st.metric("上市", f"{twse_count} 檔")
            with col2:
                tpex_count = len(df[df['市場'] == '上櫃'])
                st.metric("上櫃", f"{tpex_count} 檔")
        
        # 分類顯示結果
        st.markdown("---")
        
        # 🔥 強勢訊號
        strong = df[df['訊號強度'] >= 2]
        if not strong.empty:
            st.markdown("### 🔥 強勢訊號（多重確認）")
            st.dataframe(strong, use_container_width=True, height=300)
        
        # ⚡ 中等訊號
        medium = df[df['訊號強度'] == 1]
        if not medium.empty:
            st.markdown("### ⚡ 中等訊號（單一確認）")
            st.dataframe(medium, use_container_width=True, height=300)
        
        # 💡 初期訊號
        weak = df[df['訊號強度'] == 0]
        if not weak.empty:
            st.markdown("### 💡 初期訊號（僅MACD金叉）")
            with st.expander("點擊展開查看"):
                st.dataframe(weak, use_container_width=True, height=300)
        
        # 下載CSV
        st.markdown("---")
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下載完整結果 (CSV)",
            data=csv,
            file_name=f"monthly_macd_full_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # 個股詳細分析
        st.markdown("---")
        st.markdown("### 🔍 個股詳細分析")
        
        stock_options = [f"{row['股票代號']} - {row['股票名稱']} ({row['市場']})" 
                        for _, row in df.iterrows()]
        
        if stock_options:
            selected_stock = st.selectbox("選擇股票查看月線圖", stock_options)
            
            if selected_stock:
                stock_code = selected_stock.split(' - ')[0]
                stock_name = selected_stock.split(' - ')[1].split(' (')[0]
                market = selected_stock.split('(')[1].split(')')[0]
                
                # 抓取該股票的月線數據
                if market == '上市':
                    full_code = f"{stock_code}.TW"
                else:
                    full_code = f"{stock_code}.TWO"
                
                data = StockScanner.fetch_monthly_data(full_code)
                
                if data is not None:
                    # 計算指標
                    data = StockScanner.calculate_monthly_macd(data)
                    data = StockScanner.calculate_monthly_kd(data)
                    data = StockScanner.calculate_monthly_rsi(data)
                    
                    # 顯示該股詳細資訊
                    stock_info = df[df['股票代號'] == stock_code].iloc[0]
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("市場", stock_info['市場'])
                    with col2:
                        st.metric("現價", f"${stock_info['現價']:.2f}")
                    with col3:
                        st.metric("月MACD", f"{stock_info['月MACD']:.4f}")
                    with col4:
                        st.metric("訊號強度", f"{stock_info['訊號強度']}")
                    with col5:
                        st.metric("MACD位階", stock_info['MACD位階'])
                    
                    st.info(f"✅ 確認訊號: {stock_info['確認訊號']}")
                    
                    # 繪製圖表
                    fig = plot_monthly_chart(data, stock_code, stock_name)
                    st.pyplot(fig)
                else:
                    st.error("無法載入該股票的月線數據")
        
        # 投資建議
        st.markdown("---")
        st.markdown("### 💡 投資建議")
        
        st.markdown("""
        #### 🎯 完整掃描結果解讀：
        
        1. **優先順序**
           - 🔥 強勢訊號 > ⚡ 中等訊號 > 💡 初期訊號
           - MACD > 0 > MACD < 0
           - K值低檔（<30）> 中檔（30-60）> 高檔（>60）
        
        2. **市場差異**
           - 上市股：流動性佳，資訊透明
           - 上櫃股：波動較大，需注意流動性
        
        3. **產業分散**
           - 不要集中單一產業
           - 建議配置 3-5 個不同產業
        
        4. **進場策略**
           - 分批進場（3-5次）
           - 第一批：強勢訊號 30%
           - 第二批：週線確認 30%
           - 第三批：突破前高 40%
        
        5. **風險控管**
           - 單一股票不超過總資金 20%
           - 設定停損：跌破前月低 5-8%
           - 定期檢視（每月一次）
        """)
    
    else:
        # 初始畫面
        st.markdown("""
        ### 👋 歡迎使用完整版月MACD掃描器！
        
        #### ⭐ 完整版特色：
        
        - ✅ **支援全部上市櫃股票**（約1900檔）
        - ✅ **快速/完整雙模式**
        - ✅ **即時顯示掃描結果**
        - ✅ **自動抓取最新股票清單**
        - ✅ **市場分類統計**
        
        #### 🚀 兩種掃描模式：
        
        | 模式 | 股票數 | 時間 | 適合對象 |
        |------|--------|------|----------|
        | 🚀 快速模式 | ~70檔 | 3-5分鐘 | 日常監控 |
        | 🔍 完整模式 | ~1900檔 | 30-60分鐘 | 深度挖掘 |
        
        #### 💡 使用建議：
        
        1. **平時用快速模式**
           - 涵蓋主要權值股、熱門股
           - 快速掌握市場動態
        
        2. **週末用完整模式**
           - 挖掘冷門潛力股
           - 全面性的市場掃描
        
        3. **搭配使用效果最佳**
           - 快速模式做日常監控
           - 完整模式做週末研究
        
        #### 📊 掃描範圍：
        
        **快速模式（70檔）**
        - 🏢 大型權值股（台積電、鴻海等）
        - 💻 熱門電子股
        - 🚢 航運三雄
        - 🏦 金融股
        - 🏭 傳產龍頭
        
        **完整模式（1900檔）**
        - 📈 所有上市股票（~1000檔）
        - 📉 所有上櫃股票（~900檔）
        - 🔍 包含冷門、小型股
        
        ---
        
        ### 🎯 開始使用：
        
        1. 在左側選擇「快速模式」或「完整模式」
        2. 設定篩選條件（建議先用預設值）
        3. 點擊「🚀 開始掃描」
        4. 等待掃描完成
        5. 查看結果並下載 CSV
        
        準備好了嗎？選擇模式後點擊開始掃描吧！ 🚀
        """)


if __name__ == "__main__":
    main()
