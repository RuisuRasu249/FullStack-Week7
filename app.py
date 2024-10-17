from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import string

app = Flask(__name__)

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB
businesses = db.biz

@app.route("/api/v1.0/businesses", methods=['GET'])
def show_allbusinesses():
    page_num, page_size = 1,10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_num = int(request.args.get('ps'))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for business in businesses.find().skip(page_start).limit(page_size):
        business['_id'] = str(business['_id'])
        for review in business['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(business)
    return make_response(jsonify(data_to_return), 200)

@app.route("/api/v1.0/businesses/<string:id>", methods=['GET'])
def show_one_business(id):
    if len(id) != 24 or not all(c in string.hexdigits for c in id):
        return make_response( jsonify( {"error" : "Invalid Business ID"} ), 404 )
    business = businesses.find_one({'_id' :  ObjectId(id)})
    if id in businesses:
        business['id'] = str(business['_id'])
        for review in business['reviews']:
            review['_id'] = str(review['_id'])
        return make_response( jsonify(  businesses[id] ), 200 )
    else:
        return make_response( jsonify( {"error" : "Invalid Business ID"} ), 404 )

@app.route("/api/v1.0/businesses", methods=["POST"])
def add_business():
    if 'name' in request.form and 'town' in request.form and 'rating' in request.form:
        new_business = {
                        'name' : request.form['name'],
                        'town' : request.form['town'],
                        'rating' : request.form['rating'],
                        'reviews' : []
        }
        new_business_id = businesses.insert_one(new_business)
        new_business_link  = "http://localhost:5000/api/v1.0/businesses/" \
            + str(new_business_id.inserted_id)
        return make_response( jsonify( {"url" : new_business_link} ), 201 )
    else:
        return make_response( jsonify( {"error" : "Missing Form Data"} ), 404 )

@app.route("/api/v1.0/businesses/<string:id>", methods=["PUT"])
def edit_business(id):
    if 'name' in request.form and 'town' in request.form and 'rating' in request.form:
        result = businesses.update_one( {'_id' : ObjectId(id) }, {
            "$set": {
                "name": request.form['name'],
                "town": request.form['town'],
                "rating": request.form['rating']
            }
        })
        if result.matched_count == 1:
            edited_business_link= "http://localhost:5000/api/v1.0/businesses/" + id
            return make_response( jsonify( {"url" : edited_business_link} ), 200 )
        else:
            return make_response( jsonify( {"error" : "Invalid Business ID"} ), 404 )
    else:
        return make_response( jsonify( {"error" : "Missing Form Data"} ), 404 )

@app.route("/api/v1.0/businesses/<string:id>", methods=["DELETE"])
def delete_business(id):
    result = businesses.delete_one({"_id" : ObjectId(id)})
    if id in businesses:
        return make_response( jsonify( {} ), 200)
    else:
        return make_response( jsonify( {"error" : "Invalid Business ID"} ), 404 )

@app.route("/api/v1.0/businesses/<string:b_id>/reviews", methods=["POST"])
def add_new_review(id):
    new_review = {
        '_id' : ObjectId(),
        'username' : request.form['username'],
        'comment' : request.form['comment'],
        'stars' : request.form['stars']
    }
    businesses.update_one({"_id" : ObjectId(id)}, {
        "$push" : {"reviews" : new_review}
    })
    new_review_link= "http://localhost:5000/api/v1.0/businesses/" \
        + id + "/reviews/" + str(new_review['_id'])
    return make_response( jsonify( { "url" : new_review_link} ), 201 )

@app.route("/api/v1.0/businesses/<string:id>/reviews", methods=["GET"])
def fetch_all_reviews(id):
    data_to_return = []
    business = businesses.find_one({"_id" : ObjectId(id)}, {"reviews":1, "_id":0})
    for review in business['reviews']:
        review['_id'] = str(review['_id'])
        data_to_return.append(review)

    return make_response( jsonify( data_to_return ), 200 )

@app.route("/api/v1.0/businesses/<string:b_id>/reviews/<string:r_id>", methods=["GET"])
def fetch_one_review(b_id, r_id):
    business = businesses.find_one({"reviews._id" : ObjectId(r_id)},{
        "id": 0, "reviews.$":1
    })
    if business is None:
        return make_response(jsonify({"error" : "Invalid Business ID or Review ID"}), 404)
    business['reviews'][0]['_id'] = str(business['reviews'][0]['_id'])
    return make_response( jsonify( business['reviews'][0] ), 200)

@app.route("/api/v1.0/businesses/<string:b_id>/reviews/<string:r_id>", methods=["PUT"])
def edit_review(b_id, r_id):
    edit_review = {
        "reviews.$.username" : request.form['username'],
        "reviews.$.comment" : request.form['comment'],
        "reviews.$.stars" : request.form['stars']
    }
    businesses.update_one({
        "reviews._id" : ObjectId(r_id)
    }, {
        "$set" : edit_review
    })
    edited_review_url = "http://localhost:5000/api/v1.0/businesses/" \
        + b_id + "/reviews/" + r_id
    return make_response( jsonify( {"url" : edited_review_url} ), 200)

@app.route("/api/v1.0/businesses/<string:b_id>/reviews/<string:r_id>", methods=["DELETE"])
def delete_review(b_id, r_id):
    businesses.update_one({
        "_id" : ObjectId(b_id)
    }, {
        "$pull" : {"reviews" : {"_id" : ObjectId(r_id)}}
    })
    return make_response( jsonify( {} ), 200)


if __name__=="__main__":
    app.run(debug = True)