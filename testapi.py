import requests

# مقداردهی کلید API
API_KEY = "f66319b75a0e480787a741f94f3cfae5"
BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"


def search_recipe(query):
    """جستجوی غذا بر اساس نام"""
    params = {
        "query": query,
        "number": 5,  # تعداد نتایج
        "apiKey": API_KEY
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get("results", [])
    else:
        print(f"خطا در دریافت داده‌ها: {response.status_code}")
        return []


# تست اسکریپت
if __name__ == "__main__":
    query = input("نام غذا را وارد کنید: ")
    recipes = search_recipe(query)

    if recipes:
        for recipe in recipes:
            print(f"🍽 نام: {recipe['title']}")
            print(f"🆔 ID: {recipe['id']}")
            print(f"🖼 تصویر: {recipe.get('image', 'ندارد')}")
            print("-" * 40)
    else:
        print("❌ هیچ نتیجه‌ای یافت نشد!")
