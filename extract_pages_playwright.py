# extract_pages_playwright.py
# الاستخدام:
# 1. حرّر قيم CONFIG في الأعلى (ما عدا اليوزرنيم والباسورد).
# 2. اضبط متغيرات البيئة لبيانات الدخول قبل التشغيل:
#    (Windows CMD):
#    set HIMIT_USERNAME=your_username
#    set HIMIT_PASSWORD=your_password
#    (Linux/Mac):
#    export HIMIT_USERNAME=your_username
#    export HIMIT_PASSWORD=your_password
# 3. ثبّت المكتبات اللازمة:
#    pip install playwright pillow
#    playwright install chromium
# 4. شغّل السكربت:
#    python extract_pages_playwright.py

import asyncio
import os
import base64
import re
from io import BytesIO
from playwright.async_api import async_playwright
from PIL import Image

# ==============================================================================
# قسم CONFIG (الإعدادات)
# ==============================================================================
CONFIG = {
    # يجب تغيير هذه الروابط والمعلومات لتناسب الموقع المستهدف
    "LOGIN_URL": "https://",
    "BOOK_URL": "https://",
    
    # !! بيانات الدخول الآمنة !!
    # يتم قراءة هذه البيانات من متغيرات البيئة (Environment Variables)
    # لا تكتب بياناتك الحساسة هنا أبداً
    "USERNAME": os.environ.get("HIMIT_USERNAME"),
    "PASSWORD": os.environ.get("HIMIT_PASSWORD"),
    
    "OUTPUT_DIR": "pages",  # مجلد لحفظ صور الصفحات
    "MAX_NO_NEW_ROUNDS": 6,  # عدد الدورات المسموح بها بدون صور جديدة قبل التوقف
    "INITIAL_WAIT": 25,  # ثواني الانتظار المبدئية لتحميل الصفحة
    "CLICK_WAIT": 0.6,  # زمن الانتظار القصير بعد الضغط
    "HEADLESS": False,  # إذا كان False يفتح المتصفح أمام المستخدم (للمراجعة)
    "SELECTORS": {
        "email": "input[name=email]",
        "password": "input[name=password]",
        "submit": "button[type=submit]",
        # يجب تعديل هذا ليطابق العنصر الذي يحتوي على صورة الكتاب (غالباً <img>)
        "flipbook": "#flipbook img",
        # يجب تعديل هذا ليطابق زر "التالي"
        "next": "#nextBtn"
    }
}

# ==============================================================================
# دوال مساعدة
# ==============================================================================

async def save_data_image(src: str, filename: str) -> bool:
    """
    يحفظ الصورة المشفرة بصيغة data:image/...;base64,... إلى ملف.
    يدعم صيغ مثل webp, png, jpeg.
    
    :param src: السلسلة النصية للـ data URI (مثل 'data:image/webp;base64,...').
    :param filename: اسم الملف المراد حفظ الصورة فيه (مع التمديد).
    :return: True إذا تم الحفظ بنجاح، False خلاف ذلك.
    """
    # التحقق من أن السلسلة تبدأ بـ data:image
    if not src.startswith("data:image"):
        print(f"    [خطأ] المصدر ليس data URI: {src[:50]}...")
        return False
    
    try:
        # استخراج نوع الصورة وتشفير base64
        match = re.match(r"data:image/(\w+);base64,(.*)", src)
        if not match:
            print(f"    [خطأ] صيغة data URI غير متوقعة.")
            return False
            
        mime_type, base64_data = match.groups()
        image_data = base64.b64decode(base64_data)
        
        # استخدام PIL (Pillow) لمعالجة الصورة وحفظها (مهم للتحويلات والتأكد)
        image = Image.open(BytesIO(image_data))
        
        # بناء المسار الكامل للملف
        full_path = os.path.join(CONFIG["OUTPUT_DIR"], filename)
        
        # تحديد الصيغة المناسبة للحفظ
        save_format = mime_type.upper() if mime_type.lower() in ['jpeg', 'png', 'webp'] else 'PNG'
        
        image.save(full_path, format=save_format)
        
        return True
        
    except Exception as e:
        print(f"    [خطأ] فشل في حفظ الصورة {filename}: {e}")
        return False


# ==============================================================================
# الدالة الرئيسية للتشغيل
# ==============================================================================

async def run():
    """
    الدالة الرئيسية التي تنفذ عملية تسجيل الدخول، استخراج الصور، والتقليب.
    """
    
    # !! التحقق من وجود بيانات الدخول !!
    if not CONFIG["USERNAME"] or not CONFIG["PASSWORD"]:
        print("❌ خطأ فادح: لم يتم العثور على متغيرات البيئة HIMIT_USERNAME أو HIMIT_PASSWORD.")
        print("  يرجى إعدادهما قبل تشغيل السكربت.")
        print("  (مثال للـ Windows: set HIMIT_USERNAME=your_user)")
        print("  (مثال للـ Linux/Mac: export HIMIT_USERNAME=your_user)")
        return

    # التأكد من وجود مجلد الإخراج
    os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
    
    # مجموعات لتتبع صور الصفحات التي تم حفظها بالفعل لمنع التكرار
    saved_page_sources = set()
    total_saved_pages = 0
    rounds_without_new = 0
    
    # تشغيل Playwright
    async with async_playwright() as p:
        # 1. فتح المتصفح (Chromium)
        browser = await p.chromium.launch(headless=CONFIG["HEADLESS"])
        context = await browser.new_context()
        page = await context.new_page()

        print(f"✅ تم فتح المتصفح (headless={CONFIG['HEADLESS']}).")

        # 2. تسجيل الدخول
        try:
            print(f"⏳ الذهاب إلى صفحة تسجيل الدخول: {CONFIG['LOGIN_URL']}")
            await page.goto(CONFIG["LOGIN_URL"])

            # ملء الحقول والضغط على زر الدخول
            await page.fill(CONFIG["SELECTORS"]["email"], CONFIG["USERNAME"])
            await page.fill(CONFIG["SELECTORS"]["password"], CONFIG["PASSWORD"])
            print("  تم ملء بيانات الدخول.")
            
            # انتظار التنقل بعد الضغط على زر الإرسال
            async with page.expect_navigation():
                await page.click(CONFIG["SELECTORS"]["submit"])
            
            print("✅ تم تسجيل الدخول بنجاح (مفترض).")

        except Exception as e:
            print(f"❌ حدث خطأ أثناء تسجيل الدخول: {e}")
            await browser.close()
            return
            
        # 3. الانتقال إلى صفحة الكتاب
        print(f"⏳ الانتقال إلى صفحة الكتاب: {CONFIG['BOOK_URL']}")
        await page.goto(CONFIG["BOOK_URL"])
        
        # 4. الانتظار المبدئي لتحميل المكونات الثقيلة للكتاب (flipbook)
        print(f"⏳ انتظار {CONFIG['INITIAL_WAIT']} ثانية لتحميل الصفحة...")
        await asyncio.sleep(CONFIG["INITIAL_WAIT"])
        
        # حلقة جمع الصفحات الرئيسية
        iteration = 1
        while rounds_without_new < CONFIG["MAX_NO_NEW_ROUNDS"]:
            print("-" * 50)
            print(f"⚙️ بدء الدورة رقم: {iteration}")
            
            new_found_in_round = 0
            
            # 5. جمع كل الصور داخل العنصر المحدد
            # قد يعيد المحدد صوراً متعددة (مثل الصفحة اليسرى واليمنى)
            flipbook_images = await page.locator(CONFIG["SELECTORS"]["flipbook"]).all()
            
            if not flipbook_images:
                print("⚠️ لم يتم العثور على أي عناصر مطابقة لمحدد flipbook. توقف.")
                break
                
            print(f"  تم العثور على {len(flipbook_images)} صورة في هذه الصفحة.")
            
            # معالجة الصور واستخلاصها
            for i, img_locator in enumerate(flipbook_images):
                # استخراج محتوى خاصية src
                img_src = await img_locator.get_attribute("src")
                
                if img_src and img_src.startswith("data:image"):
                    # 7. تجنب التكرار (استخدام المصدر كبصمة)
                    if img_src not in saved_page_sources:
                        # إنشاء اسم ملف فريد
                        filename = f"page_{len(saved_page_sources) + 1:04d}.webp"
                        
                        # 6. حفظ الصورة
                        if await save_data_image(img_src, filename):
                            saved_page_sources.add(img_src)
                            total_saved_pages += 1
                            new_found_in_round += 1
                            print(f"  ✅ تم حفظ صورة جديدة: {filename}")
                        
            
            # تحديث عداد الدورات بدون صور جديدة
            if new_found_in_round == 0:
                rounds_without_new += 1
            else:
                rounds_without_new = 0
            
            # طباعة تقدم الدورة
            print(f"[iter {iteration}] new_found={new_found_in_round}, total_saved={total_saved_pages}, rounds_without_new={rounds_without_new}")
            
            # التحقق من شرط التوقف
            if rounds_without_new >= CONFIG["MAX_NO_NEW_ROUNDS"]:
                print(f"🛑 تم الوصول إلى {CONFIG['MAX_NO_NEW_ROUNDS']} دورة بدون صفحات جديدة. التوقف التلقائي.")
                break
            
            # 8. الضغط على زر "التالي" (أو السهم الأيمن)
            # نفضل الضغط على الزر إذا كان متاحاً
            next_button_locator = page.locator(CONFIG["SELECTORS"]["next"])
            if await next_button_locator.count():
                print(f"  ⏳ الضغط على زر 'التالي' ({CONFIG['SELECTORS']['next']}).")
                await next_button_locator.click()
            else:
                # محاولة استخدام السهم الأيمن كبديل
                print("  ⚠️ محاولة إرسال مفتاح السهم الأيمن (Right Arrow Key).")
                await page.keyboard.press("ArrowRight")
            
            # انتظار قصير بعد الضغط للسماح بالتقليب
            await asyncio.sleep(CONFIG["CLICK_WAIT"])
            
            iteration += 1

        # 10. طباعة رسالة الانتهاء
        print("=" * 50)
        print(f"✅ Collection finished. Total unique pages saved: {total_saved_pages}")
        print(f"  الملفات محفوظة في المجلد: {os.path.abspath(CONFIG['OUTPUT_DIR'])}")
        print("  الآن يمكنك مراجعة المتصفح المفتوح (إذا كان HEADLESS=False).")
        
        # إبقاء المتصفح مفتوحًا للمراجعة إذا لم يكن نمط العرض صامتاً
        if not CONFIG["HEADLESS"]:
            print("  اضغط Ctrl+C في الطرفية لإغلاق المتصفح و الخروج.")
            # انتظر إلى الأبد حتى يتم مقاطعة السكربت يدوياً
            await asyncio.Future() 

# تشغيل الدالة الرئيسية
if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nتم إيقاف السكربت يدوياً.")
    except Exception as e:
        print(f"\nحدث خطأ غير متوقع: {e}")