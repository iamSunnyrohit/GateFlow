from fastapi import FastAPI, HTTPException


app = FastAPI(
    title="GateFlow Product Service",
    version="1.0.0",
)


products = [
    {
        "id": 1,
        "name": "MacBook Pro",
        "category": "Electronics",
        "price": 1999,
    },
    {
        "id": 2,
        "name": "Mechanical Keyboard",
        "category": "Accessories",
        "price": 129,
    },
    {
        "id": 3,
        "name": "Wireless Mouse",
        "category": "Accessories",
        "price": 79,
    },
]


@app.get("/")
async def root():

    return {
        "service": "product-service",
        "status": "running",
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "product-service",
    }


@app.get("/products")
async def get_products():

    return {
        "service": "product-service",
        "total": len(products),
        "products": products,
    }


@app.get("/products/{product_id}")
async def get_product(product_id: int):

    product = next(
        (
            item for item in products
            if item["id"] == product_id
        ),
        None,
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product
