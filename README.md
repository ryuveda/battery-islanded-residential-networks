# battery-islanded-residential-networks
Open-source simulation framework for battery-supported islanded operation in residential distribution networks using OpenDSS and Python.

## English

This project simulates a low-voltage residential microgrid using OpenDSS and Python. The main goal is to see how photovoltaic (PV) systems and a mobile
battery help the network keep working when faults happen and the system has to run in islanded mode.

The code runs several predefined scenarios and automatically creates clear,publication-ready plots showing:
- How power is shared between PV, battery, and loads  
- How voltages change across the network  
- How the battery state of charge (SoC) evolves over time  

# Files

master.dss
loadShapes.dss
lines.dss
loads.dss
generators.dss
run_scenarios.py


# How to Run

1. Install Python and OpenDSS.  
2. Install Python packages:
pip install opendssdirect numpy matplotlib
3. Put all files in the same folder.  
4. Run:

python run_scenarios.py

# Scenarios

- Scenario 1 – No support: Fault happens, no PV and no battery.  
- Scenario 2 – Battery only: Battery supports the system after a fault.  
- Scenario 3 – PV + Battery: PV and battery work together in islanded mode.  
- Scenario 4 – Multiple faults: Several faults and reconnections during the day.  

# Output

For each scenario you get:
- Power balance plot  
- Voltage band + mean voltage plot  
- Battery SoC plot  

These figures are ready to use in reports or papers.

# Notes

- Simulation runs with 1-minute resolution (1440 steps per day).  
- Nominal voltage is 230 V.  
- Battery keeps a reserve SoC to avoid deep discharge.  


# Türkçe

Bu proje, OpenDSS ve Python kullanarak alçak gerilimli bir konut mikroşebekesini simüle eder. Temel amaç, arızalar meydana geldiğinde ve sistem adalı moda
geçtiğinde, fotovoltaik (PV) sistemler ile mobil bir bataryanın şebekenin çalışmaya devam etmesine nasıl yardımcı olduğunu incelemektir.

Kod, önceden tanımlanmış birkaç senaryoyu çalıştırır ve otomatik olarak makale ve raporlarda kullanılabilecek net grafikler üretir:
- Gücün PV, batarya ve yükler arasında nasıl paylaşıldığı  
- Şebeke genelinde gerilimlerin nasıl değiştiği  
- Bataryanın doluluk oranının (SoC) zamanla nasıl davrandığı  

# Dosyalar

master.dss
loadShapes.dss
lines.dss
loads.dss
generators.dss
buscoords.csv
run_scenarios.py
results/



# Nasıl Çalıştırılır?

1. Python ve OpenDSS’i kur.  
2. Gerekli Python paketlerini yükle:
pip install opendssdirect numpy matplotlib

3. Tüm dosyaları aynı klasöre koy.  
4. Çalıştır:
python run_scenarios.py

# Senaryolar

- Senaryo 1 – Destek yok: Arıza olur, PV ve batarya yoktur.  
- Senaryo 2 – Sadece batarya: Arızadan sonra batarya sistemi destekler.  
- Senaryo 3 – PV + Batarya: Adalı modda PV ve batarya birlikte çalışır.  
- Senaryo 4 – Çoklu arıza: Gün içinde birden fazla arıza ve yeniden bağlanma olur.  

# Çıktılar

Her senaryo için:
- Güç dengesi grafiği  
- Gerilim bandı + ortalama gerilim grafiği  
- Batarya SoC grafiği  




        
- Simülasyon 1 dakikalık çözünürlükle çalışır (günde 1440 adım).  
- Nominal gerilim 230 V kabul edilmiştir.  
- Batarya, derin deşarjı önlemek için bir SoC rezervi bırakır. 
