from flask import Flask, render_template, request, redirect, url_for, session, Blueprint

cart_bp = Blueprint("cart", __name__)
cart_bp.secret_key = "elevate-retail-secret-key"


#temp promo codes for testing
PROMO_CODES = {
    "SAVE10": 0.10,
    "SAVE20": 0.20,
    "NEW5": 5.00
}

#calculates cart totals (promo, discount, tax, shipping)
def calculate_cart_totals(cart_items, promo_code=None):
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)

    discount = 0.00
    if promo_code:
        promo_code = promo_code.upper().strip()
        promo_value = PROMO_CODES.get(promo_code)

        if isinstance(promo_value, float) and promo_value < 1:
            discount = subtotal * promo_value
        elif isinstance(promo_value, (int, float)):
            discount = float(promo_value)

    discounted_subtotal = max(subtotal - discount, 0)
    tax_rate = 0.07
    sales_tax = discounted_subtotal * tax_rate
    shipping = 0.00
    total = discounted_subtotal + sales_tax + shipping

    return subtotal, discount, sales_tax, shipping, total

# cart page route
@cart_bp.route("/cart")
def cart():
    if "cart" not in session:  #temp data
        session["cart"] = []

    promo_code = session.get("promo_code", "")
    cart_items = session.get("cart", [])

    subtotal, discount, sales_tax, shipping, total = calculate_cart_totals(
        cart_items,
        promo_code
    )

    # cart data sent to HTML template
    return render_template(
        "cart.html",
        cart=cart_items,
        subtotal=subtotal,
        discount=discount,
        sales_tax=sales_tax,
        shipping=shipping,
        total=total,
        promo_code=promo_code
    )


# route to item quantity update
@cart_bp.route("/update_cart", methods=["POST"])
def update_cart():
    product_name = request.form["product_name"]
    quantity = int(request.form["quantity"])

    cart_items = session.get("cart", [])  # gets current cart

    # finds matching item and updates
    for item in cart_items:
        if item["name"] == product_name:
            if quantity > 0:
                item["quantity"] = quantity
            else:
                cart_items.remove(item)
            break

    session["cart"] = cart_items  # saves updated cart
    return redirect(url_for("cart.cart"))  # back to cart page

#route for promo
@cart_bp.route("/apply_promo", methods=["POST"])
def apply_promo():
    promo_code = request.form.get("promo_code", "").strip().upper()

    if promo_code in PROMO_CODES:
        session["promo_code"] = promo_code
    else:
        session["promo_code"] = ""

    return redirect(url_for("cart.cart"))

# route for completely removing item
@cart_bp.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    product_name = request.form["product_name"]  # get product
    cart_items = session.get("cart", [])  # current cart

    cart_items = [item for item in cart_items if item["name"] != product_name]  # keeps all but removed

    # save and return
    session["cart"] = cart_items
    return redirect(url_for("cart.cart"))


# route to clear cart and reload
@cart_bp.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    session.pop("promo_code", None)
    return redirect(url_for("cart.cart"))

@cart_bp.route("/payment")
def payment():
    cart_items = session.get("cart", [])
    promo_code = session.get("promo_code", "")

    subtotal, discount, sales_tax, shipping, total = calculate_cart_totals(
        cart_items,
        promo_code
    )

    return render_template(
        "payment.html",
        cart=cart_items,
        subtotal=subtotal,
        discount=discount,
        sales_tax=sales_tax,
        shipping=shipping,
        total=total,
        promo_code=promo_code
    )

@cart_bp.route("/order_confirmation")
def order_confirmation():
    payment_method = request.args.get("payment_method", "N/A")
    promo_code = session.get("promo_code", "")
    cart_items = session.get("cart", [])

    subtotal, discount, sales_tax, shipping, total_paid = calculate_cart_totals(
        cart_items,
        promo_code
    )

    order = {
        "order_number": "ER123456",
        "date": "April 2, 2026",
        "customer_name": "Test Customer",
        "payment_method": payment_method,
        "subtotal": subtotal,
        "discount": discount,
        "tax": sales_tax,
        "total_paid": total_paid
    }

    order_items = []
    for item in cart_items:
        order_items.append({
            "image_url": item["image"],
            "product_name": item["name"],
            "description": item["description"],
            "quantity": item["quantity"],
            "line_total": item["price"] * item["quantity"]
        })

    return render_template(
        "order_confirmation.html",
        order=order,
        order_items=order_items
    )
