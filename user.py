from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from db import get_db_connection

user_bp = Blueprint('user', __name__)
user_bp.secret_key = "elevate-retail-secret-key"


@user_bp.route('/profile')
@login_required
def profile():
    conn = get_db_connection()  # CHANGED: open a fresh connection for this request
    cursor = conn.cursor()  # CHANGED: create a fresh cursor

    cursor.execute("""
        SELECT First_Name, Last_Name, Email, Phone, Membership_Level, Created_At
        FROM Customer WHERE Customer_ID = %s
    """, (current_user.id,))
    row = cursor.fetchone()

    cursor.execute("""
        SELECT Address_ID, Address_Line_l, Address_Line_2, City, State, Zip_Code, Country
        FROM Customer_Address WHERE Customer_ID = %s AND Deleted_At IS NULL
    """, (current_user.id,))
    addresses = cursor.fetchall()

    cursor.close()  # CHANGED: close cursor after queries
    conn.close()  # CHANGED: close connection after queries

    customer = {
        "first_name": row[0], "last_name": row[1],
        "email": row[2], "phone": row[3],
        "membership_level": row[4], "created_at": row[5],
    }
    address_list = [
        {"id": a[0], "line1": a[1], "line2": a[2],
         "city": a[3], "state": a[4], "zip": a[5], "country": a[6]}
        for a in addresses
    ]

    return render_template('profile.html', customer=customer, addresses=address_list)


@user_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    conn = get_db_connection()  # CHANGED: open a fresh connection for update
    cursor = conn.cursor()  # CHANGED: create a fresh cursor

    first = request.form.get('first_name').strip()
    last = request.form.get('last_name').strip()
    email = request.form.get('email').strip().lower()
    phone = request.form.get('phone', '').strip()

    cursor.execute("""
        UPDATE Customer SET First_Name=%s, Last_Name=%s, Email=%s, Phone=%s,
        Updated_At=UTC_TIMESTAMP()
        WHERE Customer_ID=%s
    """, (first, last, email, phone or None, current_user.id))

    conn.commit()  # CHANGED: commit using the fresh connection
    cursor.close()  # CHANGED: close cursor after update
    conn.close()  # CHANGED: close connection after update

    flash('Profile updated successfully.')
    return redirect(url_for('user.profile'))


@user_bp.route('/profile/address/add', methods=['POST'])
@login_required
def add_address():
    conn = get_db_connection()  # CHANGED: open a fresh connection for insert
    cursor = conn.cursor()  # CHANGED: create a fresh cursor

    cursor.execute("""
        INSERT INTO Customer_Address
        (Address_Line_l, Address_Line_2, City, State, Zip_Code, Country, Customer_ID)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        request.form.get('line1').strip(),
        request.form.get('line2', '').strip() or None,
        request.form.get('city').strip(),
        request.form.get('state').strip(),
        request.form.get('zip').strip(),
        request.form.get('country').strip(),
        current_user.id
    ))

    conn.commit()  # CHANGED: commit using the fresh connection
    cursor.close()  # CHANGED: close cursor after insert
    conn.close()  # CHANGED: close connection after insert

    flash('Address added.')
    return redirect(url_for('user.profile'))


@user_bp.route('/profile/address/delete', methods=['POST'])
@login_required
def delete_address():
    conn = get_db_connection()  # CHANGED: open a fresh connection for delete/update
    cursor = conn.cursor()  # CHANGED: create a fresh cursor

    address_id = request.form.get('address_id')
    cursor.execute("""
        UPDATE Customer_Address SET Deleted_At=UTC_TIMESTAMP()
        WHERE Address_ID=%s AND Customer_ID=%s
    """, (address_id, current_user.id))

    conn.commit()  # CHANGED: commit using the fresh connection
    cursor.close()  # CHANGED: close cursor after update
    conn.close()  # CHANGED: close connection after update

    flash('Address removed.')
    return redirect(url_for('user.profile'))


@user_bp.route('/profile/membership/update', methods=['POST'])
@login_required
def update_membership():
    from flask import session

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Membership_Level
        FROM Customer
        WHERE Customer_ID = %s
    """, (current_user.id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    current_level = row[0] if row and row[0] else "Bronze"
    selected_level = request.form.get('membership_level', 'Bronze')

    membership_prices = {
        "Bronze": 0,
        "Silver": 30,
        "Gold": 60,
        "Platinum": 100
    }

    valid_levels = list(membership_prices.keys())
    if selected_level not in valid_levels:
        selected_level = "Bronze"

    current_price = membership_prices.get(current_level, 0)
    selected_price = membership_prices.get(selected_level, 0)

    #downgrade or same level updates immediately
    if selected_price <= current_price:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Customer
            SET Membership_Level = %s,
                Updated_At = UTC_TIMESTAMP()
            WHERE Customer_ID = %s
        """, (selected_level, current_user.id))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Membership updated successfully.')
        return redirect(url_for('user.profile'))

    #upgrade saves choice in session and send user to cart
    session["selected_membership_level"] = selected_level
    flash(f'Upgrade selected. The price difference for {selected_level} will be added at checkout.')
    return redirect(url_for('cart.cart'))


@user_bp.route('/order_history')
@login_required
def order_history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # pull all orders for the logged in customer, newest first
    cursor.execute("""
        SELECT
            o.Order_ID,
            o.Order_Date,
            o.Order_Status,
            o.Fulfillment_Status,
            p.Method AS Payment_Method,
            COALESCE(SUM(oi.Amount + oi.Tax), 0) AS Order_Total
        FROM `Order` o
        LEFT JOIN Payment p
            ON o.Order_ID = p.Order_ID
        LEFT JOIN Order_Item oi
            ON o.Order_ID = oi.Order_ID
        WHERE o.Customer_ID = %s
        GROUP BY
            o.Order_ID,
            o.Order_Date,
            o.Order_Status,
            o.Fulfillment_Status,
            p.Method
        ORDER BY o.Order_Date DESC
    """, (current_user.id,))

    orders = cursor.fetchall()

    # pull each order's items to be shown under that order
    for order in orders:
        if order["Order_Date"]:
            order["Formatted_Order_Date"] = order["Order_Date"].strftime("%B %d, %Y at %I:%M %p")
        else:
            order["Formatted_Order_Date"] = "N/A"

        cursor.execute("""
            SELECT
                oi.Quantity,
                oi.Amount,
                oi.Tax,
                pr.Product_Name,
                pr.Product_Description,
                pr.Image_URL
            FROM Order_Item oi
            JOIN Inventory i
                ON oi.Inventory_ID = i.Inventory_ID
            JOIN Product pr
                ON i.Product_ID = pr.Product_ID
            WHERE oi.Order_ID = %s
        """, (order["Order_ID"],))

        items = cursor.fetchall()

        order["items"] = []
        for item in items:
            order["items"].append({
                "name": item["Product_Name"],
                "description": item["Product_Description"],
                "image": item["Image_URL"],
                "quantity": item["Quantity"],
                "line_total": float(item["Amount"] + item["Tax"])
            })

    cursor.close()
    conn.close()

    return render_template("order_history.html", orders=orders)