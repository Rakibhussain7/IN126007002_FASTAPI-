from fastapi import FastAPI, Query, Response, status
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


#Pydantic model for new product
class NewProduct(BaseModel):
    name: str
    price: int
    id:int
    category: str
    in_stock: bool = True




class CartItem(BaseModel):
    product_id: int
    quantity: int


class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str




products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 1499, "category": "Electronics", "in_stock": False},
    {"id": 7, "name": "Webcam", "price": 999, "category": "Electronics", "in_stock": True},
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

# GET /orders → list all orders
@app.get("/orders")
def get_orders():

    if not orders:
        return {"message": "No orders found"}

    return {
        "total_orders": len(orders),
        "orders": orders
    }

# PATCH /orders/{order_id}/confirm
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}
    return {"error": "Order not found"}

#End point -12 : add new product
@app.get("/products")
def get_products():
    return products


@app.post("/products")
def add_product(new_product: NewProduct, response: Response):

    # Check for duplicate name (case-insensitive)
    existing_names = [p['name'].lower() for p in products]

    if new_product.name.lower() in existing_names:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Product with this name already exists"}

    # Auto-generate next ID
    next_id = max(p['id'] for p in products) + 1

    product = {
        "id": next_id,
        "name": new_product.name,
        "price": new_product.price,
        "category": new_product.category,
        "in_stock": new_product.in_stock
    }

    products.append(product)

    response.status_code = status.HTTP_201_CREATED

    return {
        "message": "Product added",
        "product": product
    }



# End point -13 : update product price and stock status
from fastapi import HTTPException

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    price: Optional[int] = Query(None),
    in_stock: Optional[bool] = Query(None)
):
    for product in products:
        if product["id"] == product_id:

            if price is not None:
                product["price"] = price

            if in_stock is not None:
                product["in_stock"] = in_stock

            return product

    raise HTTPException(status_code=404, detail="Product not found")

# End point -14 : delete a product
@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):

    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return {"message": f"Product '{product['name']}' deleted"}

    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": "Product not found"}




# End point -15 : product audit
@app.get('/products/audit')
def get_audit():
    in_stock_list = [p for p in products if p['in_stock']]
    stock_value = sum(p['price'] * 10 for p in in_stock_list)
    priciest = max(products, key=lambda p: p['price'])
    return {"total_products": len(products), "in_stock_count": len(in_stock_list), 
    "out_of_stock_count": len(products) - len(in_stock_list), 
    "out_of_stock_names": [p['name'] for p in products if not p['in_stock']],
    "total_stock_value": stock_value,
    "most_expensive": {'name': priciest['name'], 'price': priciest['price']}
    }

# Discount endpoint
@app.put("/products/discount")
def bulk_discount(
    category: str = Query(..., description="Category to discount"),
    discount_percent: int = Query(..., ge=1, le=99, description="% off"),
):

    updated = []

    for p in products:
        if p["category"].lower() == category.lower():
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": f"No products found in category: {category}"}

    return {
        "message": f"{discount_percent}% discount applied to {category}",
        "updated_count": len(updated),
        "updated_products": updated,
    }
# End point  : get product by ID
@app.get("/products/{product_id}")
def get_product(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")






#Cart management endpoints
# Cart storage for tracking cart items
cart = []

@app.post("/cart/add")
def add_to_cart(item: CartItem, response: Response):

    product = next((p for p in products if p["id"] == item.product_id), None)

    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}

    if not product["in_stock"]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": f"{product['name']} is out of stock"}

    #  Check if product already in cart
    for cart_item in cart:
        if cart_item["product_id"] == item.product_id:

            cart_item["quantity"] += item.quantity
            cart_item["subtotal"] = cart_item["price"] * cart_item["quantity"]

            return {
                "message": "Cart updated",
                "cart_item": cart_item
            }

    #  If product NOT already in cart
    subtotal = product["price"] * item.quantity

    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "price": product["price"],
        "quantity": item.quantity,
        "subtotal": subtotal
    }

    cart.append(cart_item)

    return {
        "message": f"{product['name']} added to cart",
        "cart_item": cart_item
    }

# View cart
@app.get("/cart")
def view_cart():

    total = sum(item["subtotal"] for item in cart)

    return {
        "cart_items": cart,
        "total_items": len(cart),
        "grand_total": total
    }


# Checkout
@app.post("/cart/checkout")
def checkout(checkout_data: CheckoutRequest, response: Response):

    global order_counter

    if not cart:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Cart is empty"}

    placed_orders = []
    grand_total = 0

    for item in cart:

        order = {
            "order_id": order_counter,
            "customer_name": checkout_data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "delivery_address": checkout_data.delivery_address,
            "total_price": item["subtotal"],
            "status": "confirmed"
        }

        orders.append(order)
        placed_orders.append(order)

        grand_total += item["subtotal"]
        order_counter += 1

    cart.clear()

    response.status_code = status.HTTP_201_CREATED

    return {
        "message": "Checkout successful",
        "orders_placed": placed_orders,
        "grand_total": grand_total
    }


# Remove item from cart
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int, response: Response):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": f"{item['product_name']} removed from cart"}

    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": "Product not found in cart"}