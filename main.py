from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "elevate-retail-secret-key"

#home route (sends straight to cart poage right now)
@app.route("/")
def home():
    return redirect(url_for("cart"))

#cart page route
@app.route("/cart")
def cart():
    if "cart" not in session: #temp data
        session["cart"] = [
            {
                "name": "RJ Flat Screen TV",
                "description": "A sleek flat screen TV for your home entertainment setup",
                "price": 199.99,
                "image": "https://images.pexels.com/photos/28195650/pexels-photo-28195650.jpeg",
                "quantity": 2
            },
            {
                "name": "VR Headset",
                "description": "A headset that let's you experience VR worlds",
                "price": 299.99,
                "image": "https://images.pexels.com/photos/14785828/pexels-photo-14785828.jpeg",
                "quantity": 1
            }
        ]

    cart_items = session.get("cart", []) #gets cart items
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items) #subtotal

    tax_rate = 0.07 #sales tax
    sales_tax = subtotal * tax_rate

    shipping = 0.00 #temp shipping (waiting for infor from shipping team on prices)
    total = subtotal + sales_tax + shipping #final total

    #cart data sent to HTML template
    return render_template(
        "cart.html",
        cart=cart_items,
        subtotal=subtotal,
        sales_tax=sales_tax,
        shipping=shipping,
        total=total
    )

#route to item quantity update
@app.route("/update_cart", methods=["POST"])
def update_cart():
    product_name = request.form["product_name"]
    quantity = int(request.form["quantity"])

    cart_items = session.get("cart", []) #gets current cart

    #finds matching item and updates
    for item in cart_items:
        if item["name"] == product_name:
            if quantity > 0:
                item["quantity"] = quantity
            else:
                cart_items.remove(item)
            break

    session["cart"] = cart_items #saves updated cart
    return redirect(url_for("cart")) #back to cart page

#route for completely removing item
@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    product_name = request.form["product_name"] #get product
    cart_items = session.get("cart", []) #current cart

    cart_items = [item for item in cart_items if item["name"] != product_name] #keeps all but removed

    #save and return
    session["cart"] = cart_items
    return redirect(url_for("cart"))

#route to clear cart and reload
@app.route("/clear_cart")
def clear_cart():
    session.pop("cart", None) #removes cart session
    return redirect(url_for("cart")) #redirects back to cart page


if __name__ == "__main__":
    app.run(debug=True)