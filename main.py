import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Review, Order, Newsletter, ContactMessage

app = FastAPI(title="ZÈLE Ecommerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class ObjectIdStr(BaseModel):
    id: str

def oid(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

@app.get("/")
def read_root():
    return {"brand": "ZÈLE", "message": "Ecommerce backend running"}

# Products
@app.get("/api/products", response_model=List[Product])
def list_products(category: Optional[str] = None, featured: Optional[bool] = None):
    q = {}
    if category:
        q["category"] = {"$regex": f"^{category}$", "$options": "i"}
    if featured is not None:
        q["is_featured"] = bool(featured)
    docs = get_documents("product", q)
    products: List[Product] = []
    for d in docs:
        d.pop("_id", None)
        products.append(Product(**d))
    return products

@app.post("/api/products", status_code=201)
def create_product(product: Product):
    existing = db["product"].find_one({"slug": product.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    insert_id = create_document("product", product)
    return {"id": insert_id}

@app.get("/api/products/{slug}")
def get_product(slug: str):
    doc = db["product"].find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

# Reviews
@app.get("/api/products/{product_id}/reviews")
def get_reviews(product_id: str):
    reviews = get_documents("review", {"product_id": product_id})
    for r in reviews:
        r["id"] = str(r.pop("_id", ""))
    return reviews

@app.post("/api/products/{product_id}/reviews", status_code=201)
def add_review(product_id: str, review: Review):
    if review.product_id != product_id:
        raise HTTPException(status_code=400, detail="Mismatched product_id")
    rid = create_document("review", review)
    return {"id": rid}

# Orders
@app.post("/api/orders", status_code=201)
def create_order(order: Order):
    calc_subtotal = sum(i.price * i.quantity for i in order.items)
    if abs(calc_subtotal - order.subtotal) > 0.01:
        raise HTTPException(status_code=400, detail="Subtotal mismatch")
    if abs(order.subtotal + order.shipping_cost - order.total) > 0.01:
        raise HTTPException(status_code=400, detail="Total mismatch")
    oid_str = create_document("order", order)
    return {"id": oid_str, "status": "received"}

# Newsletter
@app.post("/api/newsletter", status_code=201)
def subscribe(news: Newsletter):
    existing = db["newsletter"].find_one({"email": news.email})
    if existing:
        return {"status": "already_subscribed"}
    nid = create_document("newsletter", news)
    return {"status": "subscribed", "id": nid}

# Contact
@app.post("/api/contact", status_code=201)
def contact(msg: ContactMessage):
    cid = create_document("contactmessage", msg)
    return {"status": "received", "id": cid}

# Seed sample data
@app.post("/api/seed")
def seed():
    samples = [
        Product(
            title="Cap-Toe Oxford in Nero",
            slug="cap-toe-oxford-nero",
            description="Handmade cap-toe Oxford crafted in premium full-grain calfskin. Goodyear welted for longevity and comfort.",
            short_description="Handmade cap-toe Oxford in black calfskin",
            price=495.0,
            category="formal",
            colors=["nero", "ebony"],
            sizes=[39,40,41,42,43,44,45],
            images=[
                "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?q=80&w=1200&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1593032457861-1f1f86c52a3e?q=80&w=1200&auto=format&fit=crop"
            ],
            leather="Full-grain calfskin",
            craftsmanship="Goodyear welt • Hand-burnished",
            is_featured=True
        ),
        Product(
            title="Handstitched Loafer in Chestnut",
            slug="handstitched-loafer-chestnut",
            description="Classic penny loafer with meticulous hand-stitching and cushioned insole for all-day ease.",
            short_description="Handstitched chestnut loafer",
            price=425.0,
            category="casual",
            colors=["chestnut", "mahogany"],
            sizes=[39,40,41,42,43,44,45],
            images=[
                "https://images.unsplash.com/photo-1598866594230-a7c12756260f?q=80&w=1200&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1560365163-3e8d64e762ef?q=80&w=1200&auto=format&fit=crop"
            ],
            leather="Antiqued calf",
            craftsmanship="Hand-stitched apron • Blake construction",
            is_featured=True
        ),
        Product(
            title="Wholecut in Espresso",
            slug="wholecut-espresso",
            description="Sculpted from a single piece of leather. Minimal seams, maximal elegance.",
            short_description="Wholecut in deep espresso",
            price=545.0,
            category="formal",
            colors=["espresso"],
            sizes=[39,40,41,42,43,44,45],
            images=[
                "https://images.unsplash.com/photo-1520975682031-c5815e43a916?q=80&w=1200&auto=format&fit=crop"
            ],
            leather="Museum calf",
            craftsmanship="Hand-dyed patina • Goodyear welt",
            is_featured=False
        )
    ]
    created = 0
    for p in samples:
        if not db["product"].find_one({"slug": p.slug}):
            create_document("product", p)
            created += 1
    return {"seeded": created}

# Health & schema
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
