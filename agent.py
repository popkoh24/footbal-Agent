from google import genai
import os
import re
from concurrent import futures

# ====== تنظیمات کلیدی ======
os.environ["GEMINI_API_KEY"] = "AIzaSyAQN8kVaZ9CiSl0EUY-Ib7hx4voA0EuwLs"

# ====== راه‌اندازی کلاینت ======
api_client = genai.Client()

def get_ai_response(query_text):
    result = api_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query_text
    )
    return result.text


# ====== مدیریت وضعیت جلسه ======
class TravelSession:
    def setup(self):
        self.user_prefs = {}    
        self.chat_log = []      
        self.travel_plan = ""   


current_session = TravelSession()
current_session.setup()

# ====== بررسی امنیتی ======
RESTRICTED_TERMS = ["مرز", "خطرناک", "قاچاق", "جنگ"]

def validate_input(user_message):
    for term in RESTRICTED_TERMS:
        if term in user_message:
            return False, "⚠️ این درخواست قابل پذیرش نمی‌باشد."
    return True, ""

# ====== تحلیل‌گر ترجیحات ======
def parse_user_preferences(input_text):
    detected_prefs = {}
    
    dietary_terms = ["گیاهخوار", "وجترین"]
    transport_terms = ["پیاده", "پیاده‌روی"]
    time_patterns = ["چهارروزه", "۲ روزه", "2 روزه", "۱ روزه", "1 روزه"]
    city_terms = ["تهران", "اصفهان", "شیراز", "مشهد"]
    
    for term in dietary_terms:
        if term in input_text:
            detected_prefs["diet_type"] = "vegetarian"
            break
    
    for term in transport_terms:
        if term in input_text:
            detected_prefs["movement_mode"] = "walking"
            break
    
    numbers_found = re.findall(r'\d+', input_text)
    if numbers_found:
        detected_prefs["financial_limit"] = int(numbers_found[0])
    
    if "چهارروزه" in input_text:
        detected_prefs["duration"] = 4
    elif any(day_term in input_text for day_term in ["۲ روزه", "2 روزه"]):
        detected_prefs["duration"] = 2
    elif any(day_term in input_text for day_term in ["۱ روزه", "1 روزه"]):
        detected_prefs["duration"] = 1
    
    for city in city_terms:
        if city in input_text:
            detected_prefs["destination"] = city
            break
    
    return detected_prefs

# ====== گردآورندگان اطلاعات ======
def get_sightseeing_info(preferences):
    target_city = preferences.get('destination', 'تهران')
    return get_ai_response(f"جاذبه‌های دیدنی و تاریخی {target_city} را با جزئیات مختصر فهرست کن.")

def get_dining_info(preferences):
    city_name = preferences.get('destination', 'تهران')
    if preferences.get("diet_type") == "vegetarian":
        return get_ai_response(f"نام و مشخصات مکان‌های گیاهخواری در {city_name} را بیان کن.")
    return get_ai_response(f"غذاهای بومی و مکان‌های غذایی معروف {city_name} را معرفی کن.")

def get_mobility_info(preferences):
    city_name = preferences.get('destination', 'تهران')
    if preferences.get("movement_mode") == "walking":
        return get_ai_response(f"مسیرهای مناسب گردش پیاده در {city_name} را پیشنهاد بده.")
    return get_ai_response(f"راه‌های جابجایی برای سیاحان در {city_name} کدام‌اند؟")

def gather_information_parallel(preferences):
    with futures.ThreadPoolExecutor() as executor:
        task1 = executor.submit(get_sightseeing_info, preferences)
        task2 = executor.submit(get_dining_info, preferences)
        task3 = executor.submit(get_mobility_info, preferences)
        return {
            "places": task1.result(),
            "dining": task2.result(),
            "mobility": task3.result()
        }

# ====== تولید برنامه سفر ======
def create_travel_schedule(preferences, gathered_data):
    day_count = preferences.get("duration", 1)
    query = f"""
    با توجه به داده‌های زیر، برنامه‌ای دقیق برای {day_count} روز سفری طراحی کن:

    مکان‌های دیدنی:
    {gathered_data['places']}

    گزینه‌های غذایی:
    {gathered_data['dining']}

    راه‌های جابجایی:
    {gathered_data['mobility']}

    محدوده بودجه: {preferences.get('financial_limit', 'تعیین نشده')} میلیون تومان
    """
    return get_ai_response(query)

# ====== بهبود برنامه ======
def refine_travel_plan(initial_plan):
    for iteration in range(2):
        evaluation = get_ai_response(f"این برنامه سفری را ارزیابی کرده و نقاط قوت و ضعف آن را بگو:\n{initial_plan}")
        if "عالی" in evaluation or "کامل" in evaluation or "مناسب" in evaluation:
            break
        initial_plan = get_ai_response(f"با در نظر گرفتن این ارزیابی، برنامه را بهینه کن:\nارزیابی:\n{evaluation}\nبرنامه موجود:\n{initial_plan}")
    return initial_plan

# ====== بخش اصلی برنامه - دریافت ورودی از کاربر ======
def main():
    print("=" * 50)
    print("🌍 برنامه‌ریز سفر هوشمند")
    print("=" * 50)
    print("\nلطفاً درخواست سفر خود را وارد کنید (مثال: یک سفر ۳ روزه گیاهخوار به تهران با بودجه ۵ میلیون تومان)")
    
    # دریافت ورودی از کاربر
    user_request = input("\n📝 درخواست شما: ")
    
    # بررسی امنیتی
    is_valid, message = validate_input(user_request)
    if not is_valid:
        print(f"\n{message}")
        return
    
    print("\n⏳ در حال پردازش درخواست شما...")
    
    # استخراج ترجیحات
    preferences = parse_user_preferences(user_request)
    print(f"✅ ترجیحات تشخیص داده شده: {preferences}")
    
    # ذخیره در وضعیت جلسه
    current_session.user_prefs = preferences
    current_session.chat_log.append(f"کاربر: {user_request}")
    
    # جمع‌آوری اطلاعات
    print("🔍 در حال جمع‌آوری اطلاعات...")
    research_data = gather_information_parallel(preferences)
    
    # ساخت برنامه
    print("📅 در حال ساخت برنامه سفر...")
    itinerary = create_travel_schedule(preferences, research_data)
    
    # بهینه‌سازی برنامه
    print("✨ در حال بهینه‌سازی برنامه...")
    final_itinerary = refine_travel_plan(itinerary)
    
    # ذخیره و نمایش نتایج
    current_session.travel_plan = final_itinerary
    current_session.chat_log.append(f"سیستم: برنامه سفر تولید شد")
    
    print("\n" + "=" * 50)
    print("✅ برنامه سفر نهایی:")
    print("=" * 50)
    print(final_itinerary)
    print("=" * 50)
    
    # ذخیره در فایل
    with open("travel_plan.txt", "w", encoding="utf-8") as f:
        f.write(final_itinerary)
    print("📁 برنامه در فایل 'travel_plan.txt' ذخیره شد.")

# ====== اجرای برنامه ======
if __name__ == "__main__":
    main()