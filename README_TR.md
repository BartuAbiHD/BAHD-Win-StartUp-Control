# BAHD Win StartUp Control

<div align="center">
  <p>Modern, hafif ve güçlü bir Windows başlangıç ve hizmet yöneticisi.</p>
</div>

*Bu belgeyi diğer dillerde okuyun: [English](README.md)*

<div align="center">
  <img width="800" alt="Dashboard Ekran Görüntüsü" src="https://github.com/user-attachments/assets/00e518f4-06e2-4633-aff8-addc30dfaa5a" />
</div>

## Özellikler

BAHD Win StartUp Control, Python ve PyWebView ile geliştirilmiş, gücünü Tailwind CSS'ten alan modern ve şık bir arayüze sahip bir sistem aracıdır (v1.0.0).

- **🚀 Dashboard (Kontrol Paneli)**: Windows başlangıç sürecinde otomatik olarak çalışan programları yönetin. Tek tıklamayla devre dışı bırakın/etkinleştirin ve sistem yüklerini (impact) analiz edin.
- **⚙️ Sistem Hizmetleri**: Windows arka plan servislerini görüntüleyin ve yönetin. Servisleri kolayca başlatın veya durdurun (Yönetici yetkisi gerektirebilir).
- **🗄️ Kayıt Defteri (Registry)**: Sistem kararlılığını korumak için gelişmiş başlangıç kayıt defteri yollarını salt-okunur (read-only) güvenli bir ortamda görüntüleyin.
- **📝 Sistem Kayıtları (Logs)**: Uygulamanın gerçek zamanlı loglarını ve sistem olaylarını doğrudan arayüzden takip edin.
- **🌍 Çoklu Dil Desteği (i18n)**: Hem **Türkçe** hem de **İngilizce** dillerini anında değiştirebilme imkanı.
- **🎨 Temalar**: Yerleşik **Karanlık Tema** (varsayılan) ve **Açık Tema** desteği.
- **📦 İçe/Dışa Aktar**: Başlangıç listelerinizi yedeklemek için dışa aktarın veya konfigürasyonları geri yüklemek için içe aktarın.

## Mimari

Uygulama, eski Tkinter GUI yapısından çıkarak `pywebview` kullanan modern web tabanlı bir arayüze geçiş yapmıştır.
- **Backend**: Python 3 (`winreg` ile kayıt defteri işlemleri, `psutil` ile servis takibi).
- **Frontend**: Vanilla JavaScript (SPA mimarisi), HTML5 ve Tailwind CSS (CDN üzerinden).

## Kurulum ve Çalıştırma

### Gereksinimler
- Windows 10/11
- Python 3.8+ (Kaynak koddan çalıştırılacaksa)

### Kaynak Koddan Çalıştırma
1. Dosyaları indirin veya repoyu klonlayın.
2. Sanal ortam (virtual environment) oluşturup aktif edin (önerilir).
3. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
4. Uygulamayı başlatın:
   ```bash
   python advanced_startup_manager.py
   ```

### Executable (.exe) Oluşturma
PyInstaller kullanarak tek parça bir `.exe` oluşturmak için:
```bash
pyinstaller advanced_startup_manager.spec
```
Derlenmiş çalıştırılabilir dosya `dist/` klasörü içerisinde yer alacaktır.

## Sorun Giderme

- **PermissionError (Yetki Hatası)**: `HKEY_LOCAL_MACHINE` dizininde değişiklik yapmak veya sistem servislerini durdurmak Yönetici yetkisi gerektirir. Lütfen uygulamaya sağ tıklayıp **"Yönetici olarak çalıştır"**ı seçin.
- **Beyaz Ekran / Yüklenme Sorunu**: Tailwind CSS kütüphanesinin (CDN) önbelleğe alınabilmesi için ilk açılışta internet bağlantınızın olduğundan emin olun veya sisteminizde Windows WebView2 modülünün yüklü olduğunu doğrulayın.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.
