from flask import Flask, jsonify, render_template, request
import pandas as pd
import json
import sqlite3
import requests

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
    names = [row["product_name"] for row in products]
    prices = [row["product_price"] for row in products]
    # supplier_geo
    return {"products":names,"price":prices,"geolocation":location}

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
    products = pd.read_csv("data/olist_products_dataset.csv")
    if request.method == "GET":
        return render_template("products.html",products=products)
    else:
        product_id = request.form.get("product-id")
        
        products = pd.read_csv("data/olist_products_dataset.csv")
        product = products[products["product_id"] == product_id]

        product_price = product["product_weight_g"]
        product_name = product["product_category_name"].values[0]
    
        conn = get_db_connection()
        
        conn.execute("INSERT INTO cart (product_id,product_name,product_price) VALUES (?,?,?)",
                                        (str(product_id), str(product_name),int(product_price)))
                
        conn.commit()
        conn.close
        success="Added successfully"
        return render_template("products.html",products=products, success=success)
            
@app.route("/cart", methods=["GET","POST"])
def cart():
    if request.method == "GET":
        products = get_products()
        #TODO Hier alle notwendigen Daten für Modell abrufen
        # Produkt Name, Preis, GEO, Supplier ... 
        #TODO Hier API aufrufen und Modelldaten übergeben
        location = [20.33,43.22]
        modelparams = get_model_params(products, location)
        response = requests.get(f'http://127.0.0.1:5000/predict/{modelparams}')
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
            location = request.form.get("adress")

            modelparams = get_model_params(products, location)

            response = requests.get(f'http://127.0.0.1:5000/predict/{modelparams}')
            content = json.loads(response.text)
            return render_template("cart.html",products=products, eta=content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
