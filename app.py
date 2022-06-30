from flask import Flask, render_template, request
import pandas as pd
import json
import sqlite3
import requests
from datetime import datetime

#Herstellen einer Verbindung zur Sqlite Datenbank
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

#Abfrage der Produkte im Warenkorb
def get_products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM cart").fetchall()
    conn.commit()
    conn.close
    return products

#Modellparameter 
def get_model_params(products, location):
    """
        product_category_name	[x]
        customer_zip_code	[x]
        customer_state	[x]
        seller_zip_code	[x]
        seller_state	[x]
        order_weekday   [x]

        item_count	[x]
        price	[x]
        freight_value [x]	
        product_weight_g [x]	
        product_volume_cm^3 [x]	
        delivery_distance	[x]
        order_hour_of_day [x]
    """
    dt = datetime.now()
    order_weekday = dt.weekday()
    names = [row["product_name"] for row in products]
    customer_zip_code = int(location[0])
    customer_state = location[1]
    customer_city = location[2]
    seller_zip = 7070
    seller_city = "guarulhos"
    seller_state = "SP"

    prices = [row["product_price"] for row in products]
    weights = [row["product_weight_g"] for row in products]
    volumes = [row["product_volume_cm3"] for row in products]
    order_hour_of_day = dt.hour

    return {"products":names,"prices":prices,"weights":weights,"volumes":volumes, 
            "customer_zip":customer_zip_code,"customer_state":customer_state, "customer_city":customer_city,
            "seller_zip":seller_zip, "seller_city": seller_city, "seller_state":seller_state,
            "order_day":order_weekday, "order_hour":order_hour_of_day}

"""
Das Backend des beispielhaften Webshops wurde mit der Python Bibliothek Flask entwickelt. 
Über den Server werden verschiedene HTTP Anfragen beantwortet und Daten an die HTML Seite übergeben.
"""

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("base.html")

"""
Der Aufruf der Seite mit dem Index products 
GET:
    Gibt alle Produkte des Händlers in einer Tabelle aus, welche zum Verkauf stehen
    Die Daten werden aus einer CSV Datei eingelesen.
    #TODO Seller Dataset aufbereiten und in Sqlite einfügen
POST: 
    Ein POST Aufruf fügt das ausgewählte Produkt zum Warenkorb hinzu. Der Warenkorb wird durch die Sqlite Datenbanktabelle "cart"
    abgebildet. Bei erfolgreichem Ausführen der Anfrage wird eine Erfolgsmeldung ausgegeben.  
"""
@app.route("/products", methods=["GET","POST"])
def products():
    products = pd.read_csv("data/product_selection.csv")
    if request.method == "GET":
        return render_template("products.html",products=products)
    else:
        product_id = request.form.get("product-id")
        
        product = products[products["product_id"] == product_id]

        product_price = product["price"]
        product_name = product["product_category_name"].values[0]
        product_weight = product["product_weight_g"]
        product_volume = product["product_length_cm"] * product["product_height_cm"] * product["product_width_cm"]



        conn = get_db_connection()
        
        conn.execute("INSERT INTO cart (product_id,product_name,product_price, product_weight_g, product_volume_cm3) VALUES (?,?,?,?,?)",
                                        (str(product_id), str(product_name),int(product_price), int(product_weight), int(product_volume)))
                
        conn.commit()
        conn.close
        success="Added successfully"
        return render_template("products.html",products=products, success=success)
            
@app.route("/cart", methods=["GET","POST"])
def cart():
    if request.method == "GET":
        products = get_products()
        
        location = [8215,"SP","sao paulo"]
        modelparams = get_model_params(products, location)
        modelparams = json.dumps(modelparams)
        response = requests.get(f'https://fsis-modell-api.herokuapp.com/predict/FSIS2022/{modelparams}')
        #response = requests.get(f'http://127.0.0.1:5000/predict/FSIS2022/{modelparams}')
        #DONE Ergebnis returnen und in html einbinden
        content = json.loads(response.text)
        return render_template("cart.html",products=products,eta=content)
    else:
        if request.form.get("delete"):
            conn = get_db_connection()
            conn.execute("DELETE FROM cart")
            conn.commit()
            conn.close 
            products = get_products()
            return render_template("cart.html",products=products)
        elif request.form.get("change"):
            products = get_products()
            location = request.form.get("adress").split(",")
            #28013, RJ, campos dos goytacazes
            modelparams = get_model_params(products, location)
            modelparams = json.dumps(modelparams)
            response = requests.get(f'https://fsis-modell-api.herokuapp.com/predict/FSIS2022/{modelparams}')    
            #response = requests.get(f'http://127.0.0.1:5000/predict/FSIS2022/{modelparams}')
            content = json.loads(response.text)
            return render_template("cart.html",products=products, eta=content)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5001)
