# English

## 1. Introduction
This application is a professional Investment Feasibility Tool designed for detailed financial analysis, risk assessment, and decision support. It supports **Unlevered** (FCFF) and **Levered** (FCFE) valuation modes, multi-currency modeling, and advanced uncertainty analysis.

## 2. System & Project Management

### 2.1. Project Structure
- **Dashboard**: The central hub to create new projects or load existing ones.
- **Active Project**: You must Create or Load a project to access the input pages.
- **Auto-Save**: Changes are stored in memory, but us the **"Save Project"** button to persist them to the database.

### 2.2. Access Control
- **Login**: Secure access with username/password.
- **Roles**:
    - **Admin/Editor**: Can create and edit projects.
    - **Viewer**: Read-only access to projects and reports.

## 3. Valuation Modes

### Mode 1: Unlevered (FCFF - Firm View)
- **Perspective**: The Project / Firm as a whole.
- **Cash Flow**: Free Cash Flow to Firm (FCFF).
- **Discount Rate**: WACC (Weighted Average Cost of Capital).
- **Formula**:  FCFF = EBIT \times (1 - Tax) + Depreciation - \Delta NWC - CAPEX
- **Use Case**: Evaluating the project's operational merit regardless of financing structure.

### Mode 2: Levered (FCFE - Equity View)
- **Perspective**: Shareholders / Investors.
- **Cash Flow**: Free Cash Flow to Equity (FCFE).
- **Discount Rate**: Cost of Equity (Ke).
- **Formula**: FCFE = Net Income + Depreciation - \Delta NWC - CAPEX + New Debt - Debt Repayment
- **Use Case**: Determining the actual cash return to investors after debt service.

## 4. Key Features

### 4.1. Project Setup
- **Granularity**: Choose **Yearly** (standard) or **Monthly** (high precision) calculation. Engine calculates at this level; reports aggregate to years for clarity.
- **Currencies**: Define a **Base Currency**. Inputs can be multi-currency (e.g. CAPEX in USD) and are converted using fixed Setup rates.
- **VAT Configuration**:
    - **Global Exemption**: Check "VAT Exemption" in Setup for a project-wide 0% VAT baseline.
    - **Item VAT**: Specific VAT rates can be set per CAPEX item (e.g., 18%, 20%).

### 4.2. Operations & Incentives
- **Products**: Define Volume, Price, Cost, and specific Growth/Escalation rates.
- **Capacity**: Sales volume is capped by `Capacity * OEE`.
- **Incentives (Grants)**: Defined in **CAPEX** page.
    - **Type**: Cash Grant.
    - **Logic**: If "Capex Reduction" is true, the grant reduces the asset's book value (depreciation base). If false, it acts as a direct Cash Inflow.
    - *Note: Corporate tax reductions are not explicitly modeled; adjust the global Tax Rate if needed.*

### 4.3. Financial Engine
- **Loans**: Support for equal payment (annuity), equal principal, and bullet repayment.
- **Working Capital**: Auto-calculated based on DSO/DIO/DPO.
- **Terminal Debt**: "Pay off" (cash outflow) or "Refinance" (exclude from final flow) at project end.

## 5. Risk & Uncertainty Analysis

### 5.1. Sensitivity (Tornado)
- **Methodology**: The system automatically tests a fixed range (**+/- 10%**) on Price, Volume, CAPEX, and OPEX.
- **Tornado Chart**: Visualizes the relative impact of these standardized shocks on NPV.

### 5.2. Monte Carlo Simulation
- **Concept**: Runs thousands of hypothetical scenarios.
- **Distributions**: Normal, **Lognormal**, Uniform, or Triangular.
- **Correlations**: Define relationships (e.g., Price vs Volume).
- **Outputs**: NPV Distribution, Probability of Profit, and Value at Risk (VaR).

## 6. Comprehensive Test Scenario: "Global Auto Parts Plant"

### Step A: Project Configuration
1. **Name**: "Global AutoParts"
2. **Horizon**: 10 Years | **Granularity**: Monthly.
3. **Currency**: EUR | **Inflation**: 2.5%.
4. **Valuation**: Levered (FCFE) | Cost of Equity: 14%.

### Step B: Investment (CAPEX) & Incentives
1. **Land**: €2,000,000 (Year 1, No VAT).
2. **Machinery**: "Robotic CNC", €5,000,000 (Year 1).
3. **Incentive**:
    - Add "Investment Grant": Amount=€500,000, Year 1.
    - Effect: Reduces Net Investment to €4.5M.

### Step C: Operations
1. **Product**: "Engine Block"
    - Vol: 10,000, Price: €800, Cost: €400.
    - Capacity: 12,000.
2. **Fixed Expense**: "Energy", €200,000/yr.

### Step D: Finance
1. **Loan**: €4,000,000, 5.5% Interest, 7 Years, 2 Years Grace.

### Step E: Analysis
1. **Check Incentives**: Confirm Net CAPEX in Cash Flow.
2. **Monte Carlo**: Run 500 iterations, apply 10% Volatility to Price. Check Profit Probability.

---

# Türkçe

## 1. Giriş
Bu uygulama, detaylı finansal analiz ve risk değerlendirmesi için tasarlanmış profesyonel bir Yatırım Fizibilite Aracıdır. **Firma Bazlı** (Unlevered/FCFF) ve **Özkaynak Bazlı** (Levered/FCFE) değerleme modlarını, çoklu para birimi modellemesini ve gelişmiş risk analizlerini destekler.

## 2. Sistem ve Proje Yönetimi

### 2.1. Proje Yapısı
- **Panel (Dashboard)**: Yeni proje oluşturulan veya mevcut projelerin yüklendiği ana ekran.
- **Aktif Proje**: Girdi sayfalarını kullanabilmek için önce bir projeyi "Yükle" veya "Oluştur" butonu ile aktif etmelisiniz.
- **Otomatik Kayıt Yok**: Değişiklikler hafızada tutulur. Veritabanına kalıcı yazmak için **"Projeyi Kaydet"** butonunu kullanın.

### 2.2. Erişim Yetkileri
- **Giriş**: Kullanıcı adı/şifre ile güvenli erişim.
- **Roller**:
    - **Yönetici/Editör**: Proje oluşturabilir, düzenleyebilir ve kaydedebilir.
    - **İzleyici**: Projeleri ve raporları sadece görüntüleyebilir.

## 3. Değerleme Modları

### Mod 1: Unlevered (FCFF - Firma Görünümü)
- **Perspektif**: Projenin/Firmanın kendisi.
- **Nakit Akışı**: Firmaya Serbest Nakit Akışı (FCFF).
- **İskonto Oranı**: AOSM / WACC.
- **Formül**:  FCFF = FVÖK \times (1 - Vergi) + Amortisman - \Delta İşl.Serm. - Yatırım 
- **Kullanım**: Finansman yapısından bağımsız, projenin operasyonel değerini görmek için.

### Mod 2: Levered (FCFE - Ortak Görünümü)
- **Perspektif**: Hissedarlar / Yatırımcılar.
- **Nakit Akışı**: Özkaynağa Serbest Nakit Akışı (FCFE).
- **İskonto Oranı**: Özkaynak Maliyeti (Ke).
- **Formül**:  FCFE = Net Kar + Amortisman - \Delta İşl.Serm. - Yatırım + Yeni Kredi - Kredi Ödemesi 
- **Kullanım**: Borç ödendikten sonra yatırımcının cebine kalan net nakdi görmek için.

## 4. Temel Özellikler

### 4.1. Proje Ayarları
- **Zaman Dilimi**: **Yıllık** (standart) veya **Aylık** (hassas). Motor, seçilen dilimde hesaplar; raporlar genellikle yıllık özette sunulur.
- **Birimler**: Raporlama için tek bir **Baz Para Birimi** seçilir. Girdiler farklı kurlarda olabilir; sistem sabit kurlar ile dönüştürür.
- **KDV Yapısı**:
    - **İstisna**: Ayarlar'da "KDV İstisnası Var mı?" kutucuğu, TÜM proje için KDV'yi %0 kabul eder.
    - **Kalem Bazlı**: İstisna yoksa, her CAPEX kalemi için ayrı KDV oranı (%1, %10, %20) girilebilir.

### 4.2. Operasyon ve Teşvikler
- **Ürünler**: Hacim, Fiyat, Maliyet ve Büyüme oranları tanımlayın.
- **Teşvikler (Hibeler)**: **CAPEX** (Yatırım) sayfasında tanımlanır.
    - **Mekanizma**: "Nakit Hibe" olarak eklenir. `Capex Reduction` seçilirse, varlığın defter değerini (amortisman matrahını) düşürür. Seçilmezse doğrudan Nakit Geliri sayılır.
    - *Not: Kurumlar Vergisi indirimi ayrı bir modül değildir; genel Vergi Oranını düşürerek simüle edebilirsiniz.*
- **Kapasite**: Satışlar `Kapasite * Verimlilik (OEE)` ile sınırlanır.

### 4.3. Finansal Motor
- **Krediler**: Eşit Taksit, Eşit Anapara veya Balon ödeme.
- **İşletme Sermayesi**: DSO/DIO/DPO parametreleriyle otomatik hesaplanır.
- **Vade Sonu (Terminal)**: Kalan borç, nakit akışından düşülerek kapatılabilir (Payoff) veya hariç tutulabilir (Refinance).

## 5. Risk ve Belirsizlik Analizi

### 5.1. Duyarlılık (Tornado)
- **Yöntem**: Sistem; Fiyat, Hacim, Yatırım ve Gider kalemlerini sabit **+/- %10** aralığında değiştirerek NPV etkisini ölçer.
- **Grafik**: Hangi değişkenin projeyi en çok etkilediğini gösterir.

### 5.2. Monte Carlo Simülasyonu
- **Konsept**: Binlerce senaryo çalıştırarak olasılık dağılımı çıkarır.
- **Dağılımlar**: Normal, **Lognormal**, Uniform veya Üçgen.
- **Çıktılar**: NPV Dağılımı, Kar Olasılığı ve Riske Maruz Değer (VaR).

## 6. Örnek Test Senaryosu: "Global Otomotiv Fabrikası"

### Adım A: Proje Kurulumu
1. **İsim**: "Global Otomotiv"
2. **Vade**: 10 Yıl | **Zaman**: Aylık.
3. **Para Birimi**: EUR | **Enflasyon**: %2.5.
4. **Değerleme**: Levered (Özkaynak Bazlı) | Özkaynak Maliyeti: %14.

### Adım B: Yatırım ve Teşvik
1. **Arazi**: 2,000,000 € (1. Yıl, KDV Yok).
2. **Makine**: "Robotik Hat", 5,000,000 € (1. Yıl).
3. **Teşvik**:
    - "Hibe Ekle": Tutar=500,000 €, Yıl=1.
    - Etki: Net Yatırım harcamasını 4.5M €'ya düşürür.

### Adım C: Operasyon
1. **Ürün**: "Motor Bloğu"
    - Hacim: 10,000, Fiyat: 800 €, Maliyet: 400 €.
2. **Sabit Gider**: "Enerji", 200,000 €/Yıl.

### Adım D: Finansman
1. **Kredi**: 4,000,000 €, %5.5 Faiz, 7 Yıl Vade, 2 Yıl Ödemesiz.

### Adım E: Analiz
1. **Teşvik Kontrolü**: Nakit Akım tablosunda Yatırım çıkışının netleştiğini görün.
2. **Risk Analizi**: 500 İterasyon yapın, Fiyata %10 oynaklık verin. Kâr ihtimalini kontrol edin.
