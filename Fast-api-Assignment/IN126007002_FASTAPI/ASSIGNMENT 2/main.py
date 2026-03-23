from fastapi import FastAPI, Query
from typing import Optional, List
from pydantic import BaseModel, Field

app = FastAPI()

# pydantic model
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

feedback = []

# Order storage for tracking
orders = []
order_counter = 1

# pydantic model for bulk order
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 1499, "category": "Electronics", "in_stock": False},
    {"id": 7, "name": "Webcam", "price": 999, "category": "Stationery", "in_stock": True},
]

# End point -1 : returns a welcome message
@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API!"}

# End point -2 : returns all products with total count
@app.get("/products")
def get_all_products():
    return {"products": products, "total": len(products)}

# End point -3 : filter products by category, price and stock status
@app.get("/products/filter")
def filter_products(
    category: Optional[str] = Query(None, description="Electronics or Stationery"),
    max_price: Optional[int] = Query(None, description="Maximum price"),
    min_price: Optional[int] = Query(None, description="Minimum price"),
    in_stock: Optional[bool] = Query(None, description="True = in stock only"),
):
    result = products
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {"filtered_products": result, "count": len(result)}

# End point -4 : get products by category with count
@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]
    if not result:
        return {"error": "No products found in this category"}
    return {"category": category_name, "products": result, "count": len(result)}

# End point -5 : get products that are in stock with count
@app.get("/products/in_stock")
def get_in_stock_products():
    result = [p for p in products if p["in_stock"]]
    return {"in_stock_products": result, "count": len(result)}

# End point -6 : get store summary
@app.get("/store/summary")
def store_summary():
    in_stock_count = len([p for p in products if p["in_stock"]])
    out_of_stock_count = len(products) - in_stock_count
    categories = list(set(p["category"] for p in products))
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count,
        "categories": categories
    }

# End point -7 : search products
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    keyword = keyword.lower()
    result = [p for p in products if keyword in p["name"].lower()]
    if not result:
        return {"message": "No product matched your search"}
    return {"keyword": keyword, "results": result, "total_matches": len(result)}

# End point -8 : best deals
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {"best_deals": cheapest, "premium_pick": expensive}

# Get only the price of a product
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}

# End point-9: feedback endpoint
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback),
    }

# End point -10 : summary dashboard
@app.get("/products/summary")
def product_summary():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]
    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])
    categories = list(set(p["category"] for p in products))
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories,
    }

# End point -11 : bulk order
@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed, failed, grand_total = [], [], 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
    return {"company": order.company_name, "confirmed": confirmed, "failed": failed, "grand_total": grand_total}


# Order Status Tracker
# POST /orders → create order (pending)
@app.post("/orders")
def place_order(product_id: int, quantity: int):
    global order_counter
    order = {
        "order_id": order_counter,
        "product_id": product_id,
        "quantity": quantity,
        "status": "pending"
    }
    orders.append(order)
    order_counter += 1
    return {"message": "Order placed successfully", "order": order}

# GET /orders/{order_id}
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}

# PATCH /orders/{order_id}/confirm
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}
    return {"error": "Order not found"}