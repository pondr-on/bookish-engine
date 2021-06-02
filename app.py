import os
from flask_cors import CORS, cross_origin
import openai
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import uuid
from firebase_admin import credentials, firestore, initialize_app, auth
app = Flask(__name__)
#

@app.route('/auth/enterprise', methods=['POST', 'GET'])
def create_company():
    """
        create_company(): companies can create a account.
    """
    now = datetime.now()
    try:
        data = request.json['data']
        Company_name = 'C-'+data['company_name']
        Date = datetime.timestamp(now)
        Category = data['category']
        Address = data['address']
        Phone_number = data['phone_number']
        password = data['password']
        Email = data['email']
        Person_of_contact_first = data['first_name']
        Person_of_contact_last = data['last_name']
        Company_website = data['company_website']
        Outreach_type = data['outreach_type']
        Company_logo = data['company_logo']
        beta_key = data['beta_key']
        survey_questions = data['survey_questions']
        if beta_key == "BfFQKJ9vIf":
            user = auth.create_user(phone_number = Phone_number, password = password,email=Email, display_name=Company_name)
            auth.set_custom_user_claims(user.uid, {'Enterprise': True})
            company_document = COMPANY.document(user.uid)
            company_document.set({
                'company_name' : Company_name,
                'company_id' : user.uid,
                'address' : Address,
                'phone_number' : Phone_number,
                'email' : Email,
                'person_of_contact_first' : Person_of_contact_first,
                'person_of_contact_last' : Person_of_contact_last,
                'company_website' : Company_website,
                'category' : Category,
                'date' : Date,
                'company_logo': Company_logo,
                'outreach_type': Outreach_type,
                'survey_questions': survey_questions
            })
            return jsonify({"success":True}), 200
        else:
            return jsonify("Please Enter Correct BETA Key"), 403
    except Exception as e:
        return f"An Error Occured: {e}"

""" ------------------------------------------------
PUBLIC ROUTES (AVAILABLE TO EVERYONE ON THE INTERNET)
------------------------------------------------ """
@app.route('/product/<id>/', methods=['GET'])
def get_basic_analytics(id):
    """
        get_basic_analytics(id): get basic analytics of a certain product by their ID.
    """
    try:
        todo = PRODUCT.document(id).get()
        todo2 = BASIC_ANALYTICS.document(id).get()
        return jsonify({"PRODUCT: ":todo.to_dict(),"BASIC_ANALYTICS: ": todo2.to_dict()}), 200
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/review/scrape', methods=['POST'])
def post_scrapping_link():
    """
        post_scrapping_link(): post amazon scrapping link, category, email.
    """
    now = datetime.now()
    try:
        data = request.json['data']
        link = data['link']
        email = data['email']
        category = data['category']
        date = datetime.timestamp(now)
        query_ref = SCRAPPER.where(u'link', u'==',link)
        documents = [doc.to_dict() for doc in query_ref.stream()] #this is a very expensive call
        if (len(documents) >0):
            return jsonify({"success": False}), 200
        else:
            Scrapping_document = SCRAPPER.document(str(date)+str(category))
            Scrapping_document.set({
                'email': email,
                'link': link,
                'category': category,
                'processed': False,
                'date': date,
                'ip_address':request.remote_addr
            })
            return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


"""------------------------------------------------
REVIEW GURU ROUTES (AVAILABLE TO REVIEW GURUS)
------------------------------------------------"""

@app.route('/review/create', methods=['POST'])
def create_post():
    """
        create_post() : a review guru can create a post that will be sent to the waitlist collection, review-guru/contributions, and the Posts collection.
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid  = claims['uid']
        if claims['Review-guru'] is True:
            data = request.json['data']
            created_by = data['Created_by']
            created_by_id = data['Created_by_id']
            date = datetime.timestamp(now)
            post_title = data['Post_title']
            product_name = data['Product_name']
            Summary = data['Comments']
            product_name = data['Product_name']
            product_id = data['Product_id']
            company_id = data['Company_id']
            post_id = str(created_by_id)+str(product_id)+str(date)
            questions = data['Questions']

            id_token = request.headers['Authorization']
            claims = auth.verify_id_token(id_token)
            if claims['Review-guru'] is True:
                Review_contributions = REVIEW_GURU.document(created_by_id).collection('contributions').document(product_id)
                Review_post = REVIEW_POST.document(product_id)
                Review_post.set({
                    'Created_by': created_by,
                    'Created_by_id': created_by_id,
                    'Date' : date,
                    'Product_id': product_id,
                    'Product_name': product_name,
                    'Summary': Summary,
                })
                Review_contributions.set({
                    'Created_by': created_by,
                    'Created_by_id': created_by_id,
                    'Date' : date,
                    'Product_id': product_id,
                    'Product_name': product_name,
                    'Summary': Summary,
                })
                review_guru_document = WAITLIST.document(company_id).collection(product_id).document(created_by_id)
                review_guru_document.set({
                'Created_by': created_by,
                'Created_by_id': created_by_id,
                'Date': date,
                'Questions': Questions,
                'Post_title': post_title,
                'Product_id': product_id,
                'Product_name': product_name,
                'Company_id': company_id,
                'Review_processed': False
                })
        else:
             return jsonify("You are not authorised to create a review"), 403
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/review-guru/inbox', methods=['GET'])
def get_products_inbox():
    """
        get_product_inbox() : get the list of products assigned to the review-guru.
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if(claims['Review-guru'] == True):
            query_ref = REVIEW_GURU.document(uid).collection('products-assigned').get()
            return jsonify(query_ref.to_dict()),200
        else:
            return jsonify({"success": False}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/review-guru/contributions', methods=['GET'])
def get_contributions():
    """
        get_contributions() : get the list of contributions made by a review guru
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if(claims['Review-guru'] == True):
            query_ref = REVIEW_GURU.document(uid).collection('contributions').get()
            return (jsonify(query_ref.to_dict()),200)
        else:
            return(jsonify({"response":"You are not authorised to create a review"}))
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/review-guru/suggestion', methods=['POST'])
def review_guru_suggestion():
    """
        review_guru_suggestion(): a review guru can create a suggestion and we can read through them.
    """
    now = datetime.now()
    try:
        data = request.json['data']
        comment = data['Comment']
        date = datetime.timestamp(now)
        created_by = data['Created_by']
        created_by_id = data['Created_by_id']
        category = data['Categories']
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Review-guru'] is True:
            suggestion_document = SUGGESTION.document(str(date)+str(created_by_id))
            suggestion_document.set({
                'Comment': comment,
                'Created_by': created_by,
                'Created_by_id': created_by_id,
                'Categories': category,
                'Tag': "Review_guru",
                'Date': str(date)
            })
            return jsonify({"success": True}), 200
        else:
            return(jsonify({"response":"We would love your suggestion but you need to create an account first"}))
    except Exception as e:
        return f"An Error Occured: {e}"


"""------------------------------------------------
ENTERPRISE ROUTES (AVAILABLE TO ENTPERISE CUSTOMERS)
------------------------------------------------"""
@app.route('/enterprise/suggestion', methods=['POST'])
def make_enterprise_suggestion():
    """
        make_enterprise_suggestion(): a enterpise can create a suggestion and we can read through them.
    """
    now = datetime.now()
    try:
        data = request.json['data']
        comment = data['Comment']
        date = datetime.timestamp(now)
        created_by = data['Created_by']
        created_by_id = data['Created_by_id']
        category = data['Categories']
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Enterprise'] is True:
            suggestion_document = SUGGESTION.document(str(date)+str(created_by_id))
            suggestion_document.set({
                'Comment': comment,
                'Created_by': created_by,
                'Created_by_id': created_by_id,
                'Tag': "Enterprise",
                'Date': str(date)
            })
            return jsonify({"success": True}), 200
        else:
            return(jsonify({"response":"We would love your suggestion but you need to create an account first"}), 404)
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/enterprise/product=<id>/question', methods = ['POST'])
def ask_ai_question(id):
    """
         ask_question(id): Companies can ask questions about a product using GPT-3 on their specific product.
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        data = request.json['data']
        question = request['question']
        date = datetime.timestamp(now)
        if claims['Enterpise'] is True:
            todo = GPT3QA.document(id).get().to_dict()
            if todo['company_id'] == uid:
                response = openai.Answer.create(
                    search_model="ada",
                    model="curie",
                    question=str(question),
                    file=todo['gpt3_form_id'],
                    examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
                    examples=[["What is human life expectancy in the United States?", "78 years."],
                              ["what is the population of Seattle?", "Seattle's population is 724,305"]],
                    max_tokens=40,
                    stop=["\n", "<|endoftext|>"],
                )
                todo.set({
                    str(question): response['answers'],
                }, merge=True)

                return jsonify({"Answer": response['answers']}), 200
            else:
                return (jsonify({"response":"You are not authorized to view this page"}), 403)
        else:
            return (jsonify({"response":"You are not authorized to view this page"}), 403)
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route("/enterprise/product=<id>/ai", methods=['GET'])
def get_gpt3_data(id):
    """
         get_gpt3_data(id): Companies can see GPT-3 asked questions/answers
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterpise'] is True:
            todo = GPT3QA.document(id).get().to_dict()
            if todo['company_id'] == uid:
                return (jsonify(todo),200)
            else:
                return (jsonify({"response":"You are not authorized to view this page"}), 403)
        else:
            return (jsonify({"response":"You are not authorized to view this page"}), 403)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/products', methods=['GET'])
def get_products_by_company():
    """
         get_products_by_company(id): this will be for company dashboard.
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            query_ref = PRODUCT.where(u'Company_id', u'==', uid)
            documents = [doc.to_dict() for doc in query_ref.stream()]
            return (jsonify({"company_products":documents}),200)
        else:
            return (jsonify({"response":"You are not authorized to view this page"}), 403)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/product=<id>', methods = ['GET'])
def get_advanced_analytics(id):
    """
         get_advanced_analytics(id): this will be for company dashboard, they will see the advanced analytics of a product.
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid  = claims['uid']
        if claims['Enterprise'] is True:
            todo = ADVANCED_ANALYTICS.document(id).get().to_dict()
            if todo['company_id'] == uid:
                return jsonify(todo), 200
            else:
                return (jsonify({"Access Denied"}), 403)
        else:
            return (jsonify({"response":"You are not authorized to view this specific enterpise analytics page."}), 404)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/createProduct', methods=['POST'])
def create_product():
    """
         create_product(): a product entry for a enterprise (NOT ACTIVATED FOR REVIEW GURUS ANALYTICS).
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            data = request.json['data']
            Category = data['Category']
            Company_name = data['Company_name']
            Company_id = uid
            Date = datetime.timestamp(now)
            Product_id = str(Date)+ uid
            Product_name = data['Product_name']
            Amazon_link = data['amazon_link']
            product_document = PRODUCT.document(Product_id)
            product_document.set({
                'Category' : Category,
                'Company_name': Company_name,
                'Company_id' : Company_id,
                'Product_entry_date': Date,
                'Product_id': Product_id,
                'Product_images_path': "enterpise/"+str(Product_id)+"/",
                'Product_name': Product_name,
                'Amazon_link': Amazon_link,
                'processed': False,
                'assigned' : False,
                'review_guru_analytics': False
            })
            return jsonify({"success": True}), 200
        else:
            return (jsonify({"response":"You are not authorized to view this page"}), 404)
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/enterprise/request', methods=['POST'])
def request_review_guru():
    """
         request_review_guru(): request analytics through a review guru when a product has been created.
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            data = request.json['data']
            product_id = data['Product_id']
            Stock_amount = data['Stock_amount']
            colors_offered = data['Colors_offered']
            Sizes = data['Sizes']
            Target_audience = data['Target_audience'] # this box will be used to figure out what kind of demographic is the product intended for.
            review_guru_request_date = datetime.timestamp(now)
            price = data['Price']
            product_document = PRODUCT.document(Product_id)
            product_document.set({
                "Stock_amount": Stock_amount,
                "Colors_offered": colors_offered,
                "Sizes": Sizes,
                "Target_audience": Target_audience,
                "Price": price
            }, merge=True)
            field_updates = {"review_guru_analytics": True}
            product_document.update(field_updates)

            return ({"success": True}), 200
        else:
            return ({"success": False}), 404

    except Exception as e:
        return f"An Error Occured: {e}"
