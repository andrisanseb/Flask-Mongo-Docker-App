from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, Response
import json
import os
import uuid
import time
import ast
import random


# Connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

# Choose database
db = client['DSMarkets']

# Choose collections
users = db['Users']
products = db['Products']

# Initiate Flask App
app = Flask(__name__)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)

users_sessions = {}

def create_session(username):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (username, time.time())
    return user_uuid

def is_session_valid(user_uuid):
    return user_uuid in users_sessions


# --ΑΠΛΟΣ ΧΡΗΣΤΗΣ--
#Δημιουργία απλού χρήστη
@app.route('/createUser', methods=['POST'])
def create_user():
    # Request JSON data
    data = None
    try:
        data=json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "name" in data or not "password" in data or not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    """
    Το συγκεκριμένο endpoint θα δέχεται στο body του request του χρήστη ένα json της μορφής: 
    {
        "email":"an email"
        "name":"name",
        "password": "a very secure password"
    }
    """
    # if no users exist , first one created is admin
    if(users.count()==0):
        users.insert_one({"_id":random.randint(1000000000000, 9999999999999),"name":data["name"],"email":data["email"],"password":data["password"],"category":"admin"})
        return Response(data['name'] + " was added to the MongoDB", status=200, mimetype='application/json')

    if(users.find_one({'email':data['email']}) == None):      #ψάνει αν το email που δώθηκε ήδη υπάρχει στο collection Users.Αν ΔΕΝ υπάρχει μπαίνει στην if
        # Παρακάτω γίνεται εισαγωγη του χρηστη,δημιουργειτε τυχαιο-μοναδικο 13ψηφιο κωδικο,email,name,password όπως αυτα δωθηκαν στο body, τον κατατασουμε στους απλους χρηστες και ακομα δυο πεδια που θα αναλυσουμε αργοτερα
        users.insert_one({"_id":random.randint(1000000000000, 9999999999999),"name": str(data['name']) ,"email": str(data['email']), "password": str(data['password']), "category":"simple","cart":[],"orderHistory":[]})       #δημιουργεί τον user
        # Μήνυμα επιτυχίας
        return Response(data['name'] + " was added to the MongoDB",status=200,mimetype='application/json')
    else:
        # Μήνυμα λάθους (Υπάρχει ήδη κάποιος χρήστης με αυτό το email)
        return Response("A user with the given email already exists",status=400,mimetype='application/json')


# Login στο σύστημα
@app.route('/login', methods=['POST'])
def login():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "email" in data or not "password" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    """
        Το συγκεκριμένο endpoint θα δέχεται στο body του request του χρήστη ένα json της μορφής: 
        {
            "email":"an email",
            "password": "a very secure password"
        }
    """

    if (users.find_one({'email': data['email'], 'password': data['password']}) != None):  # μπαίνει μέσα στην if μόνο εάν υπάρχει email με το συγκεκριμένο password στην βάση ( δηλαδή ΟΧΙ None)
        user_uuid = create_session(data['email'])  # ο κωδικός που θα ζητείται κάθε φορά από το σύστημα
        res = {"uuid": user_uuid, "email": data['email']}
        global current_user_email
        current_user_email= data['email']  #για επομενα ερωτηματα
        return Response(json.dumps(res), status=200, mimetype='application/json')

    else:  # Αν ΔΕΝ είναι σωστά τα στοιχεία που δώθηκαν περνάει εδώ
        # Μήνυμα λάθους (Λάθος email ή password)
        return Response("Wrong email or password. Please insert again.", status=400, mimetype='application/json')


#Αναζήτηση product
@app.route('/getProduct', methods=['GET'])
def get_product():
    # Request JSON data
    data = None
    flag=0
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')

    # ελεγχος για τι πληροφορια εδωσε ο χρηστης
    if("name" in data):
        flag=1
        x = "name"
    elif("category" in data):
        flag=1
        x="category"
    elif("_id" in data):
        flag=1
        x="_id"

    if (flag==0):
        return Response("Information incomplete", status=500, mimetype="application/json")

    """
            Το συγκεκριμένο endpoint θα δέχεται στο body του request του χρήστη ένα json της μορφής: 
            {
                "_id": 13-digit integer (χωρις "")!!!
                ή
                "name":"prod name"
                ή
                "category":"category"
            }
    """

    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        if(x=="name"):  #αν ο χρηστης εδωσε ονομα εκτελειται ο παρακατω κωδικας
            prods=[]    #αποθηκευονται τα προιοντα που θα επιστραφουν
            for p in products.find({x: data[x]},{"stock":0}).sort(x,1):     #ψαχνει ποια προιοντα εχουν ιδιο ονομα με αυτο που δωθηκε,ταξηνομημενα με βαση το ονομα
                p['_id'] = str(p['_id'])
                res = {"name":p["name"],"description":p["description"],"price":p["price"],"category":p["category"],"_id":p['_id']}
                prods.append(res)       #προσθετω τα δεδομενα του προιοντος στον πινακα prods

        elif(x=="category"):    #ιδια διαδικασια με παραπανω,αλλα εδω γινεται ταξηνομηση με βαση την τιμη
            prods = []
            for p in products.find({x: data[x]}, {"stock": 0}).sort('price', 1):
                p['_id'] = str(p['_id'])
                res = {"name": p["name"], "description": p["description"], "price": p["price"],
                       "category": p["category"], "_id": p['_id']}
                prods.append(res)

        elif(x=="_id"):
            prods=0
            p=json.dumps(products.find_one({"_id":data["_id"]}, {"stock": 0}))
            prods = ast.literal_eval(p)

        if prods==[] or prods==0:
            return Response("Data given does not correspond to any product.")

        return Response(json.dumps(prods), status=200, mimetype='application/json')


# Προσθηκη product στο καλαθι
@app.route('/addToCart', methods=['PATCH'])
def add_to_cart():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "_id" in data or not "total" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    """""
    body:
        {
            "_id": the 13-digit code  (oxi mesa se ""!!!)
            "total": ποσα τεμαχια θελω (σε int)
        } 
    """""

    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        if products.find_one({"_id":data["_id"]}) != None :
            cu=json.dumps(users.find_one({"email": current_user_email}))
            curr_user = ast.literal_eval(cu)
            cp = json.dumps(products.find_one({"_id": data["_id"]}))
            curr_prod = ast.literal_eval(cp)

            if curr_prod["stock"] < data["total"]:
                return Response("There is not enough stock to cover the ammount asked",status=500, mimetype="application/json")
            else:
                if curr_user["cart"]==[]:
                    users.update_one({"email": current_user_email},{"$set":{"cart":[data]}})
                else:
                    curr_user["cart"].append(data)
                    users.update_one({"email": current_user_email}, {"$set": {"cart": curr_user["cart"]}})


                return Response("product added to cart."+show_cart(),status=200, mimetype="application/json")
        else:
            return Response("_id given does not belong to any product",status=500, mimetype="application/json")




# Εμφάνιση καλαθιού/cart
@app.route('/showCart', methods=['GET'])
def show_cart():
    cu=json.dumps(users.find_one({"email": current_user_email}))
    curr_user = ast.literal_eval(cu)
    msg="Products and total price :"
    how_much=0
    cart_exists = "cart" in curr_user
    if(cart_exists):
        for x in range(len(curr_user["cart"])):
            _pid= curr_user["cart"][x]["_id"]
            _pammount=curr_user["cart"][x]["total"]
            cp=json.dumps(products.find_one({"_id":_pid}))
            curr_prod=ast.literal_eval(cp)
            how_much=how_much+(_pammount*curr_prod["price"])
            msg=msg+"   "+str(_pammount)+"*"+curr_prod["name"]
    how_much1=float("{:.2f}".format(how_much))
    msg=msg+"      TOTAL: "+str(how_much1)+"€"
    return msg


# Αφαίρεση προιόντος από καλάθι
@app.route('/deleteFromCart', methods=['PUT'])
def delete_from_cart():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "_id" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    """""
    body:
        {
            "_id": the 13-digit code  (oxi mesa se ""!!!)
        } 
    """""

    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        if products.find_one({"_id": data["_id"]}) != None:
            p = json.dumps(users.find_one({"email": current_user_email}))
            prods = ast.literal_eval(p)
            flag=0
            for x in range(len(prods["cart"])):  #PROSOXH mhpws den thelei -1
                flag=1
                if (prods["cart"][x]["_id"] == data["_id"]):
                    prods["cart"].pop(x)
                    users.update_one({"email": current_user_email}, {"$set": {"cart": prods["cart"]}})

            if(flag==1):
                return Response("product deleted from cart."+show_cart(), status=200, mimetype="application/json")
            else:
                return Response("_id given does not exist in cart", status=500, mimetype="application/json")
        else:
            return Response("_id given does not belong to any product of the database", status=500, mimetype="application/json")



# Αγορά
@app.route('/buy', methods=['PUT'])
def buy():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "card" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    """""
    body:
        {
            "card": the 16-digit code  (oxi mesa se ""!!!)
        } 
    """""

    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        cardstr = str(data["card"])
        if(len(cardstr)==16):
            cu = json.dumps(users.find_one({"email": current_user_email}))
            curr_user = ast.literal_eval(cu)
            if curr_user["orderHistory"] == []:
                users.update_one({"email": current_user_email}, {"$set": {"orderHistory": [curr_user["cart"]]}})

                #STOCK UPDATE-REMOVE AMMOUNT OF ITEMS BOUGHT
                for x in range(len(curr_user["cart"])):
                    _pid = curr_user["cart"][x]["_id"]
                    _pammount = curr_user["cart"][x]["total"]
                    cp = json.dumps(products.find_one({"_id": _pid}))
                    curr_prod = ast.literal_eval(cp)
                    updated_stock= curr_prod["stock"]-_pammount
                    products.update_one({"_id": _pid},{"$set":{"stock":updated_stock}})

                msg = show_cart()
                msg = msg[-15:]
                msg = "PAYMENT COMPLETE, " + msg
                users.update_one({"email": current_user_email}, {"$set": {"cart": []}})

            else:
                curr_user["orderHistory"].append(curr_user["cart"])
                users.update_one({"email": current_user_email}, {"$set": {"orderHistory": curr_user["orderHistory"]}})

                for x in range(len(curr_user["cart"])):
                    _pid = curr_user["cart"][x]["_id"]
                    _pammount = curr_user["cart"][x]["total"]
                    cp = json.dumps(products.find_one({"_id": _pid}))
                    curr_prod = ast.literal_eval(cp)
                    updated_stock = curr_prod["stock"] - _pammount
                    products.update_one({"_id": _pid}, {"$set": {"stock": updated_stock}})

                msg=show_cart()
                msg=msg[-15:]
                msg="PAYMENT COMPLETE, "+msg
                users.update_one({"email": current_user_email}, {"$set": {"cart": []}})

            return Response(msg, status=200, mimetype="application/json")
        else:
            return Response("Card code must be 16-digit long.Try again", status=200, mimetype="application/json")




# Εμφάνιση ιστορικού αγορών
@app.route('/showOrderHistory', methods=['GET'])
def show_order_history():

    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        msg = ""
        cu = json.dumps(users.find_one({"email": current_user_email}))
        curr_user = ast.literal_eval(cu)
        atLeastOne=False
        for x in range(len(curr_user["orderHistory"])):
            how_much=0
            msg_order="Order "+str(x+1)+" : "    #gia na mhn lew order 0
            for y in range(len(curr_user["orderHistory"][x])):
                atLeastOne=True
                _pid = curr_user["orderHistory"][x][y]["_id"]
                _pammount = curr_user["orderHistory"][x][y]["total"]
                cp = json.dumps(products.find_one({"_id": _pid}))
                curr_prod = ast.literal_eval(cp)
                how_much = how_much + (_pammount * curr_prod["price"])
                msg_order = msg_order + "  " + str(_pammount) + "*" + curr_prod["name"]
            how_much1 = float("{:.2f}".format(how_much))
            msg =msg+ msg_order + "   TOTAL: " + str(how_much1) + "€       "

        if(atLeastOne):
            return Response(msg, status=200, mimetype="application/json")
        else:
            return Response("No orders made", status=500, mimetype="application/json")



# Διαγραφή user
@app.route('/deleteUser', methods=['DELETE'])
def delete_student():
    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        users.delete_one({"email":current_user_email})
        return Response("User Deleted", status=200, mimetype="application/json")


#ADMIN-ENDPOINTS

# Δημιουργία product
@app.route('/createProduct', methods=['POST'])
def create_product():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "name" in data or not "price" in data or not "description" in data or not "category" in data or not "stock" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    """
        Το συγκεκριμένο endpoint θα δέχεται στο body του request του χρήστη ένα json της μορφής: 
        {   
            "name":"name",
            "price":"a float number.Without euro sign!!!",
            "description": "product description",
            "category": "product category",
            "stock": "an integer"
        }
        """
    # PREPEI NA EXEI KANEI LOGIN O ADMIN
    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)
    cu = json.dumps(users.find_one({"email": current_user_email}))
    curr_user = ast.literal_eval(cu)
    if(curr_user["category"]!="admin"):
        valid=False

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        # εκτος των τιμων που δωθηκαν στο body,δημιουργειτε και ο μοναδικος 13-ψηφιος κωδικος _id (παντα τυχαιος).
        products.insert_one({"_id":random.randint(1000000000000, 9999999999999),"name": str(data['name']), "price": float(data['price']), "description": str(data['description']),"category":str(data["category"]),"stock":int(data["stock"])})  # δημιουργεί το product

        # Μήνυμα επιτυχίας
        return Response(data['name'] + " was added to the MongoDB", status=200, mimetype='application/json')



# Διαγραφή product βάσει _id
@app.route('/deleteProduct', methods=['DELETE'])
def delete_product():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "_id" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    """""
    {
        "email":"user-email",
        "password":"user-password",
        "_id": the 13-digit code  (oxi se ""!!!)
    } 
    """""
    # PREPEI NA EXEI KANEIS LOGIN O ADMIN
    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)
    cu = json.dumps(users.find_one({"email": current_user_email}))
    curr_user = ast.literal_eval(cu)
    if (curr_user["category"] != "admin"):
        valid = False

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        flag=0
        msg = "This _id does not belong to any Product"  # το μηνυμα που θα εμφανιστει στο τελος εαν ΔΕΝ γινει διαγραφη product
        if (products.find_one({"_id": data['_id']}) != None):
            flag=1
            msg = str(data["_id"])+" was deleted from MongoDB"
            products.delete_one({"_id": data["_id"]})  # διαγραφη product

        # επιστροφή μηνήυματος με το κατάλληλλο status
        if(flag==0):
            return Response(msg, status=500, mimetype='application/json')
        else:
            return Response(msg, status=200, mimetype='application/json')


# Ενημέρωση product
@app.route('/modifyProduct', methods=['PATCH'])
def modify_product():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "_id" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    """""
    body:
        {
            "_id": the 13-digit code  (oxi se ""!!!)
            "το πεδιο που θελουμε να ενημερωσουμε" : "νεα τιμη"
            "καποιο αλλο πεδιο..." : "καποια αλλη τιμη"
        } 
    """""
    # PREPEI NA EXEI KANEIS LOGIN O ADMIN
    uuid = request.headers.get('authorization')
    valid = is_session_valid(uuid)
    cu = json.dumps(users.find_one({"email": current_user_email}))
    curr_user = ast.literal_eval(cu)
    if (curr_user["category"] != "admin"):
        valid = False

    if valid == False:
        return Response("Unauthorized", status=401)
    else:
        flag=0
        if (products.find_one({"_id": data['_id']}) != None):
            if "name" in data:
                flag=1
                products.update_one({"_id": data['_id']},{"$set":{"name":data["name"]}})
            if "price" in data:
                flag=1
                products.update_one({"_id": data['_id']},{"$set":{"price":float("{:.2f}".format(data["price"]))}})
            if "description" in data:
                flag=1
                products.update_one({"_id": data['_id']},{"$set":{"description":data["description"]}})
            if "stock" in data:
                flag=1
                products.update_one({"_id": data['_id']},{"$set":{"stock":int(data["stock"])}})

            if flag==1:
                return Response(str(data["_id"])+" was modified.", status=200, mimetype='application/json')
            else:
                return Response(str(data["_id"])+" was not modified.", status=204, mimetype='application/json')


        else:
            return Response("No product with this _id", status=400, mimetype='application/json')







# Εκτέλεση flask service σε debug mode, στην port 5000.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)