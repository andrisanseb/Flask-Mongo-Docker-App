#  Dockerized Eshop
## Flask εφαρμογή με mongoDB

#### HOW TO RUN:
Make sure you have docker and docker-compose installed.
You must git-clone the repository,cd into it,type docker-compose build and then docker-compose up.

1. $ git clone https://github.com/andrisanseb/Flask-Mongo-Docker-App.git
1. $ cd https://github.com/andrisanseb/Flask-Mongo-Docker-App.git
1. $ sudo docker-compose build
1. $sudo docker-compose up


### Setting up first user-admin: **Create user**
  - Request URL: http://localhost:5000/createUser
  - Method POST
  - Body:{
    "name":"a name",
    "email":"an email",
    "password":"safe password"
      }
      
      
##### NOTES:
- Database is empty.The first user created becomes admin. Log in is required for admins too.
- Before running any operation make sure you are logged in and that you pass the uuid as Authorization at the header.
      
      
Mandatory for both admins and simple users    
**Login:**
  - Request URL: http://localhost:5000/login
  - Method POST
  - Body:{
    "email":"email of existing user",
    "password":"his/her password"
      }


### ADMIN-ENDPOINTS:

**Product Creation:**
  - Request URL: http://localhost:5000/createProduct
  - Method POST
  - Body:{
    "name":"product name",
    "price":"product price", (eg:"price":"8.5" or "price":"2")
    "description":"explain the product",
    "category":"what kind of product is this",
    "stock":"integer number of this product available"
      }
   - Note: All fields must be defined in order to create a product. 

**Delete Product:**
  - Request URL: http://localhost:5000/deleteProduct
  - Method DELETE
  - Body:{
    "_id": 13-digit integer (WARNING:do not use "") 
      }
      

**Modify Product:**
  - Request URL: http://localhost:5000/modifyProduct
  - Method PATCH
  - Body:{
    "_id":13-digit code,
    "name":"product name",
    "price":"product price", (eg:"price":"8.5" or "price":"2")
    "description":"explain the product",
    "stock":"integer number of this product available"
      }
    - Note: _id is mandatory in the body.You can then add one or more of the above: name,price,description,stock.


### SIMPLE USER-ENDPOINTS:

**Search for Product(s):**
  - Request URL: http://localhost:5000/getProduct
  - Method GET
  - Body:{
        "_id": 13-digit integer
        "name":"prod name"
         "category":"category"
         }
   - Note: Only one of the _id,name,category must be passed in the body,based on what you are searching for.


**Add to Cart:**
  - Request URL: http://localhost:5000/addToCart
  - Method PATCH
  - Body:
        {
            "_id": the 13-digit code 
            "total": how many  
        } 
   - Warning-Note: Both _id and total must be passed as integers.

  
**Show Cart:**
  - Request URL: http://localhost:5000/showCart
  - Method GET
  - no body passed
  
  
**Delete Product from Cart:**
  - Request URL: http://localhost:5000/deleteFromCart
  - Method PUT
  - Body:
        {
            "_id": the 13-digit code 
        }


**Buy:**
  - Request URL: http://localhost:5000/buy
  - Method PUT
  - Body:{
          "card": the 16-digit code
         }


**Show All Previous Completed Orders:**
  - Request URL: http://localhost:5000/showOrderHistory
  - Method GET
  - no body passed
  

