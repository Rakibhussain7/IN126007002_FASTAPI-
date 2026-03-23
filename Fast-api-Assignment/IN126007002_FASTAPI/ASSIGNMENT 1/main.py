from fastapi import FastAPI, Query
app = FastAPI()

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price":799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen set", "price": 49  , "category": "Stationery", "in_stock": True},
    #Added 3 more products
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 1499, "category": "Electronics", "in_stock": False},
    {"id": 7, "name": "Webcam", "price": 999, "category": "Stationery", "in_stock": True},
]
#End point -1 : returns a welcome message
@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API!"}

#End point -2 : returns all products with total count
@app.get("/products")
def get_all_products():
    return {"products": products, "total": len(products)}

#End point -3 : filter products by category, price and stock status
@app.get("/products/filter")
def filter_products(
    category: str = Query(None, description="Electronics or Stationery"),
    max_price: int = Query(None, description="Maximum price"),
    in_stock: bool = Query(None, description="True = in stock only")
):
    result = products
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {"filtered_products": result, "count": len(result)}

#End point -4 : get products by category with count
@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name] 
    if not result:
         return {"error": "No products found in this category"}
    return {"category": category_name, "products": result, "count": len(result)}

#End point -5 : get products that are in stock with count
@app.get("/products/in_stock")
def get_in_stock_products():
    result = [p for p in products if p["in_stock"] == True]
    return {"in_stock_products": result, "count": len(result)}

#End point -6 : get store summary with total products, in_stock count, out_of_stock_count and categories
@app.get("/store/summary")
def store_summary():
    in_stock_count = len([p for p in products if p["in_stock"] == True])
    out_of_stock_count = len(products) - in_stock_count
    categories = list(set(p["category"] for p in products))
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count,
        "categories": categories
    }

#End point -7 : search products by keyword in name with count
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    keyword = keyword.lower()
    result = [p for p in products if keyword in p["name"].lower()]
    if not result:
        return {"message": "No product matched your search"}
    return {"keyword": keyword, "results": result, "total_matches": len(result)}

#End point -8 : get best deals (cheapest and most expensive products)
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {"best_deals": cheapest, "premium_pick": expensive}


#End point -9 : get product details by id
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"product": product}
    return {"error": "Product not found"}, 404

