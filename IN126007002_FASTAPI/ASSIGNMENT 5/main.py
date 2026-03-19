from fastapi import FastAPI, Query, Response, status, HTTPException
from typing import Optional, List
from pydantic import BaseModel, Field

app = FastAPI()

# pydantic model
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str
    contact_email: str
    items: List[OrderItem]

class NewProduct(BaseModel):
    name: str
    price: int
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
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 1499, "category": "Electronics", "in_stock": False},
    {"id": 7, "name": "Webcam", "price": 999, "category": "Electronics", "in_stock": True},
]

feedback = []
orders = []
cart = []
order_counter = 1

def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None

# End point -1 : returns a welcome message
@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API!"}

# End point -2 : returns all products with total count
@app.get("/products")
def get_all_products():
    return {"products": products, "total": len(products)}

# End point -3 : filter products
@app.get("/products/filter")
def filter_products(
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    in_stock: Optional[bool] = None,
):
    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {"products": result, "count": len(result)}

# End point -4 : search products
@app.get("/products/search")
def search_products(keyword: str):
    result = [p for p in products if keyword.lower() in p["name"].lower()]
    return {"results": result, "count": len(result)}

# End point -5 : sort products
@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price", description="price or name"),
    order: str = Query("asc", description="asc or desc"),
):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}
    if order not in ["asc", "desc"]:
        return {"error": "order must be 'asc' or 'desc'"}

    reverse = order == "desc"
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)

    return {"sort_by": sort_by, "order": order, "products": sorted_products}

# End point -6 : pagination
@app.get("/products/page")
def paginate(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    return {"page": page, "products": products[start:end], "total": len(products)}

# End point -7 : product summary
@app.get("/products/summary")
def summary():
    in_stock = [p for p in products if p["in_stock"]]
    return {
        "total_products": len(products),
        "in_stock": len(in_stock),
        "out_of_stock": len(products) - len(in_stock),
    }

# End point -8 : add product
@app.post("/products")
def add_product(new_product: NewProduct, response: Response):
    next_id = max(p["id"] for p in products) + 1

    product = {
        "id": next_id,
        "name": new_product.name,
        "price": new_product.price,
        "category": new_product.category,
        "in_stock": new_product.in_stock,
    }

    products.append(product)
    response.status_code = status.HTTP_201_CREATED
    return product


#sort products by category then price
@app.get('/products/sort-by-category')
def sort_by_category():
    result = sorted(products, key=lambda p: (p['category'], p['price'])) 
    return {'products': result, 'total': len(result)}



#end point -18 : combined search, sort, pagination
@app.get('/products/browse')
def browse_products(
    keyword: str = Query(None),
    sort_by: str = Query('price'),
    order: str = Query('asc'),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20),
):
    result = products.copy()

    # 🔍 Search
    if keyword:
        keyword = keyword.strip().lower()
        result = [
            p for p in result
            if keyword in p.get('name', '').lower()
        ]

    # 🔃 Sort
    if sort_by in ['price', 'name']:
        result = sorted(
            result,
            key=lambda p: p.get(sort_by, ''),
            reverse=(order == 'desc')
        )

    # 📄 Pagination
    total = len(result)
    start = (page - 1) * limit

    if start >= total:
        return {"message": "Page out of range"}

    paged = result[start:start + limit]

    return {
        'keyword': keyword,
        'sort_by': sort_by,
        'order': order,
        'page': page,
        'limit': limit,
        'total_found': total,
        'total_pages': (total + limit - 1) // limit,
        'products': paged,
    }


# End point -9 : update product
@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None):
    product = find_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    if price is not None:
        product["price"] = price
    if in_stock is not None:
        product["in_stock"] = in_stock

    return product

# End point -10 : delete product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    products.remove(product)
    return {"message": "Product deleted"}

# End point -11 : get product by ID
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    return product

# End point -12 : add to cart
@app.post("/cart/add")
def add_to_cart(item: CartItem):
    product = find_product(item.product_id)

    if not product:
        raise HTTPException(404, "Product not found")
    if not product["in_stock"]:
        raise HTTPException(400, "Out of stock")

    subtotal = product["price"] * item.quantity

    cart.append({
        "product_id": product["id"],
        "name": product["name"],
        "quantity": item.quantity,
        "subtotal": subtotal
    })

    return {"message": "Added to cart"}

# End point -13 : view cart
@app.get("/cart")
def view_cart():
    total = sum(item["subtotal"] for item in cart)
    return {"cart": cart, "total": total}

# End point -14 : checkout
@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):
    global order_counter

    if not cart:
        raise HTTPException(400, "Cart is empty")

    orders_created = []

    for item in cart:
        order = {
            "order_id": order_counter,
            "customer": data.customer_name,
            "total": item["subtotal"]
        }
        orders.append(order)
        orders_created.append(order)
        order_counter += 1

    cart.clear()
    return {"orders": orders_created}

# End point -15 : get orders
@app.get("/orders")
def get_orders():
    return {"orders": orders}

# End point -16 : feedback
@app.post("/feedback")
def add_feedback(data: CustomerFeedback):
    feedback.append(data.dict())
    return {"message": "Feedback submitted"}

#end point -17 : search orders by customer name
@app.get('/orders/search')
def search_orders(customer_name: str = Query(...)):
    search = customer_name.strip().lower()

    results = [
        o for o in orders
        if search in o.get('customer', '').lower()
    ]

    if not results:
        return {'message': f'No orders found for: {customer_name}'}

    return {
        'customer_name': customer_name,
        'total_found': len(results),
        'orders': results
    }


#paginate the order list
@app.get('/orders/page')
def paginate_orders(page: int = Query(1, ge=1), limit: int = Query(2, ge=1, le=10)):
    total = len(orders)
    start = (page - 1) * limit

    if start >= total:
        return {"message": "Page out of range"}

    paged_orders = orders[start:start + limit]

    return {
        'page': page,
        'limit': limit,
        'total_orders': total,
        'total_pages': (total + limit - 1) // limit,
        'orders': paged_orders
    }
