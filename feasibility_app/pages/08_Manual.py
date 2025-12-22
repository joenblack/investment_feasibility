import streamlit as st

from ui.components import ensure_state, sidebar_nav, t, bootstrap

bootstrap(require_project=False)
sidebar_nav()

st.title(t("manual_link"))

# Content Definitions
manual_en = """
## 1. Introduction
This application is a professional Investment Feasibility Tool designed for detailed financial analysis, risk assessment, and decision support. It supports **Unlevered** (FCFF) and **Levered** (FCFE) valuation modes, multi-currency modeling, and advanced uncertainty analysis.

## 2. Valuation Modes

### Mode 1: Unlevered (FCFF - Firm View)
- **Perspective**: The Project / Firm as a whole.
- **Cash Flow**: Free Cash Flow to Firm (FCFF).
- **Discount Rate**: WACC (Weighted Average Cost of Capital).
- **Formula**: $$ FCFF = EBIT \\times (1 - Tax) + Depreciation - \\Delta NWC - CAPEX $$
- **Use Case**: Evaluating the project's operational merit regardless of financing structure.

### Mode 2: Levered (FCFE - Equity View)
- **Perspective**: Shareholders / Investors.
- **Cash Flow**: Free Cash Flow to Equity (FCFE).
- **Discount Rate**: Cost of Equity (Ke).
- **Formula**: $$ FCFE = Net Income + Depreciation - \\Delta NWC - CAPEX + New Debt - Debt Repayment $$
- **Use Case**: Determining the actual cash return to investors after debt service.

## 3. Key Features

### 3.1. Project Setup
- **Granularity**: Choose between **Yearly** (standard) or **Monthly** (high precision) calculation. Note: Monthly calculations are aggregated to years for summary reports.
- **Currencies**: Define a **Base Currency** for the report. Inputs can be in different currencies (e.g., CAPEX in USD, Revenue in EUR), and the engine converts them using fixed exchange rates defined here.

### 3.2. Market & Operations (Revenue/OPEX)
- **Products**: Define multiple products with Volume, Price, Cost, and specific Growth/Escalation rates.
- **Capacity**: Sales volume is capped by `Capacity * OEE`.
- **Incentives**: Add Investment Incentives (Cash Grants, Tax Reductions) in CAPEX/OPEX pages.
- **Personnel**: Detailed payroll planning including social security taxes and annual raises.

### 3.3. Financial Engine
- **Loans**: Support for equal payment (annuity), equal principal, and bullet repayment.
- **Working Capital**: Auto-calculated based on DSO (Receivables), DIO (Inventory), and DPO (Payables).
- **Terminal Debt**: Choose to "Pay off" remaining debt at project end or "Refinance" (exclude from final cash flow).

## 4. Risk & Uncertainty Analysis
This is a comprehensive module to stress-test your assumptions.

### 4.1. Sensitivity (Tornado)
- **Auto-Derivation**: The system automatically varies Price, Volume, CAPEX, and OPEX by +/- 10% (or configurable range).
- **Tornado Chart**: Visualizes which variable has the biggest impact on NPV.

### 4.2. Monte Carlo Simulation
- **Concept**: Runs thousands of hypothetical scenarios by randomly shocking key variables.
- **Distributions**: Normal (Bell Curve), Uniform (Range), or Triangular.
- **Correlations**: Define relationships (e.g., if Price goes UP, Volume might go DOWN).
- **Outputs**:
    - **NPV Distribution**: Assessing the probability of loss (Negative NPV).
    - **Value at Risk (VaR)**: The worst-case loss at 95% confidence.

## 5. Comprehensive Test Scenario: "Global Auto Parts Plant"

To fully test the application capabilities, follow this end-to-end scenario.

### Step A: Project Configuration
1. **Name**: "Global AutoParts Plant"
2. **Horizon**: 10 Years.
3. **Granularity**: Monthly (to test precision).
4. **Currency**: EUR (Base).
5. **Inflation**: 2.5% (EUR).
6. **Valuation**: Levered (FCFE) | Cost of Equity: 14%.

### Step B: Investment (CAPEX) & Incentives
1. **Land**: "Industrial Zone Plot", €2,000,000 (Year 1, No VAT).
2. **Machinery**: "Robotic CNC Line", €5,000,000 (Year 1, VAT 0% - Incentive).
3. **Incentive**:
    - Add "Investment Grant": Type=Cash (Capex Reduction), Amount=€500,000, Year 1.

### Step C: Operations (Revenue & OPEX)
1. **Product 1**: "Engine Block (Exp)"
    - Vol: 10,000, Price: €800, Cost: €400.
    - Capacity: 12,000.
    - Terms: Advance 20%, Payment 60 Days.
2. **Product 2**: "Brake System (Loc)"
    - Vol: 50,000, Price: €50, Cost: €30.
    - Currency: TRY (Simulate multi-currency).
3. **Personnel**:
    - "Tech Team": 20 people, Cost €3,000/mo.
    - "Management": 5 people, Cost €8,000/mo.
4. **Fixed Expense**:
    - "Energy": €200,000 / year (Escalation 3% > Inflation).

### Step D: Finance
1. **Loan**: "Investment Loan"
    - Amount: €4,000,000.
    - Interest: 5.5%.
    - Term: 7 Years.
    - Grace: 2 Years.
2. **Working Capital**:
    - DSO: 45 Days, DIO: 30 Days, DPO: 60 Days.

### Step E: Analysis & Verification
1. **Check Financial Statements**: Ensure Loan Grace Period works (Interest only for Y1-Y2).
2. **Check Incentives**: Confirm CAPEX outflow is Net of Grant (€5M - €0.5M = €4.5M).
3. **Run Risk Analysis (Monte Carlo)**:
    - Settings: 500 Iterations.
    - Variables: Apply 10% Volatility to "Engine Block" Price.
    - Result: Check "Probability of Profit". If < 80%, consider hedging or reducing costs.

This scenario covers 90% of the application's logic including advanced localized tax/incentive handling.
"""

manual_tr = """
## 1. Giriş
Bu uygulama, detaylı finansal analiz, risk değerlendirmesi ve karar destek süreçleri için tasarlanmış profesyonel bir Yatırım Fizibilite Aracıdır. **Firma Bazlı** (Unlevered/FCFF) ve **Özkaynak Bazlı** (Levered/FCFE) değerleme modlarını, çoklu para birimi modellemesini ve gelişmiş risk analizlerini destekler.

## 2. Değerleme Modları

### Mod 1: Unlevered (FCFF - Firma Görünümü)
- **Perspektif**: Projenin/Firmanın kendisi (Finansman yapısından bağımsız).
- **Nakit Akışı**: Firmaya Serbest Nakit Akışı (FCFF).
- **İskonto Oranı**: AOSM / WACC (Ağırlıklı Ortalama Sermaye Maliyeti).
- **Formül**: $$ FCFF = FVÖK \\times (1 - Vergi) + Amortisman - \\Delta İşl.Serm. - Yatırım $$
- **Kullanım**: Projenin operasyonel verimliliğini, borç yapısından bağımsız değerlendirmek için.

### Mod 2: Levered (FCFE - Ortak Görünümü)
- **Perspektif**: Hissedarlar / Yatırımcılar.
- **Nakit Akışı**: Özkaynağa Serbest Nakit Akışı (FCFE).
- **İskonto Oranı**: Özkaynak Maliyeti (Ke).
- **Formül**: $$ FCFE = Net Kar + Amortisman - \\Delta İşl.Serm. - Yatırım + Yeni Kredi - Kredi Ödemesi $$
- **Kullanım**: Borç servis edildikten sonra yatırımcının cebine kalan gerçek nakdi görmek için.

## 3. Temel Özellikler

### 3.1. Proje Ayarları & Girdiler
- **Zaman Dilimi (Granularity)**: Hesaplamalar **Yıllık** (Standart) veya **Aylık** (Hassas) olarak yapılabilir. Aylık modda nakit akışları daha hassas modellenir.
- **Çoklu Para Birimi**: Raporlama için bir **Baz Para Birimi** seçilir. Girdiler farklı kurlarda (Örn: Makine USD, Satış EUR, Maaş TRY) girilebilir; motor bunları otomatik dönüştürür.

### 3.2. Operasyonel (Gelir/Gider)
- **Kapasite Limiti**: Satış hacmi `Kapasite * OEE (Verimlilik)` ile sınırlanır.
- **Teşvikler**: Yatırım Teşvik Belgesi kapsamındaki nakit hibeler veya KDV istisnaları sisteme tanımlanabilir.
- **Ödeme Vadeleri**: Ürün bazında Avans (%) ve Vade (Gün) tanımlanarak İşletme Sermayesi ihtiyacı optimize edilebilir.

### 3.3. Finansal Motor
- **Krediler**: Eşit Taksitli (Annuite), Eşit Anaparaku veya Balon (Vade sonu ödemeli) krediler. Ödemesiz dönem desteği mevcuttur.
- **Terminal Değer**: Proje sonunda kalan borcun kapatılması (Payoff) veya yeniden finanse edilmesi (Refinance) seçilebilir.

## 4. Risk ve Belirsizlik Analizi (Gelişmiş)
Yatırımın risklerini ölçmek için kapsamlı modül.

### 4.1. Duyarlılık (Tornado)
- **Otomatik Analiz**: Sistem; Fiyat, Hacim, Yatırım ve Gider kalemlerini +/- %10 (veya ayarlanabilir) oranında şoklayarak NPV etkisini ölçer.
- **Tornado Grafiği**: Hangi değişkenin proje değerini en çok etkilediğini "Kasırga" grafiğiyle gösterir.

### 4.2. Monte Carlo Simülasyonu
- **Konsept**: Binlerce farklı senaryoyu (iterasyon) rassal olarak çalıştırır.
- **Korelasyonlar**: Değişkenler arası ilişki tanımlanabilir (Örn: Fiyat artarsa Hacim düşer).
- **Çıktılar**:
    - **Kar Olasılığı**: Projenin zarar etme ihtimali nedir?
    - **Riske Maruz Değer (VaR %95)**: En kötü senaryoda kaybınız ne olur?

## 5. Kapsamlı Test Senaryosu: "Global Otomotiv Yan Sanayi"

Uygulamanın tüm özelliklerini (Teşvik, Kredi, Risk, Çoklu Döviz) test etmek için bu senaryoyu uygulayın.

### Adım A: Proje Kurulumu
1. **İsim**: "Global Otomotiv Fabrikası"
2. **Vade**: 10 Yıl.
3. **Zaman Dilimi**: Aylık (Hassasiyet testi için).
4. **Para Birimi**: EUR (Baz).
5. **Enflasyon**: %2.5 (Euro Bölgesi Enflasyonu).
6. **Değerleme**: Levered (Özkaynak Bazlı) | Özkaynak Maliyeti: %14.

### Adım B: Yatırım (CAPEX) & Teşvikler
1. **Arazi**: "OSB Arsa Tahsisi", 2,000,000 € (1. Yıl, KDV Yok).
2. **Makine**: "Robotik Montaj Hattı", 5,000,000 € (1. Yıl).
3. **Teşvik**:
    - "Yatırım Teşviki Ekle": Tip=Yatırım Teşviki (Nakit), Tutar=500,000 €, Yıl=1.
    - Not: Bu işlem yatırım nakit çıkışını netleştirecektir.

### Adım C: Operasyonlar
1. **Ürün 1**: "Motor Bloğu (İhracat)"
    - Hacim: 10,000, Fiyat: 800 €, Maliyet: 400 €.
    - Kapasite: 12,000 / Yıl.
    - Ticari: Avans %20, Vade 60 Gün.
2. **Ürün 2**: "Fren Sistemi (Yerli)"
    - Hacim: 50,000.
    - Para Birimi: TRY (Çoklu kur testi). Fiyat: 2000 TRY.
3. **Personel**:
    - "Mühendis Kadrosu": 20 Kişi, Maliyet 3,000 €/Ay.
    - "Yönetim": 5 Kişi, Maliyet 8,000 €/Ay.

### Adım D: Finansman
1. **Kredi**: "Yatırım Kredisi"
    - Tutar: 4,000,000 €.
    - Faiz: %5.5 (Yıllık).
    - Vade: 7 Yıl.
    - Ödemesiz Dönem: 2 Yıl (İnşaat süresince sadece faiz).

### Adım E: Analiz ve Doğrulama
1. **Nakit Akışını Kontrol Et**: 1. ve 2. yıllarda sadece faiz ödendiğini, 3. yıldan itibaren anapara ödemesinin başladığını "Finansal Tablolar" > "Nakit Akış" sekmesinden teyit edin.
2. **Net Yatırımı Gör**: Teşvik sayesinde yatırım çıkışının düştüğünü doğrulayın.
3. **Risk Analizi Çalıştır**:
    - "Risk Analizi" sayfasına gidin.
    - **Monte Carlo**: 500 İterasyon seçin.
    - **Değişkenler**: "Motor Bloğu" Fiyatına %10 oynaklık (volatilite) verin.
    - **Sonuç**: "Kâr Olasılığı" (Probability of Profit) %80'in üzerindeyse proje güvenlidir.
"""

if st.session_state.language == 'tr':
    st.markdown(manual_tr)
else:
    st.markdown(manual_en)

if st.session_state.language == 'tr':
    st.markdown(manual_tr)
else:
    st.markdown(manual_en)
