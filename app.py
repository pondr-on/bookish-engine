import os
from flask_cors import CORS, cross_origin
import openai
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import uuid
from firebase_admin import credentials, firestore, initialize_app, auth
app = Flask(__name__)
#import os
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def enterprise():
    """
        Home(): The Home Page For The Pondr enterprise Kubernetes Path.
    """
    return "<h1> Pondr BETA </h1>"


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
        Phone_number = data['phone_number']
        password = data['password']
        Email = data['email']
        Person_of_contact_first = data['first_name']
        Person_of_contact_last = data['last_name']
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
                'phone_number' : Phone_number,
                'email' : Email,
                'person_of_contact_first' : Person_of_contact_first,
                'person_of_contact_last' : Person_of_contact_last,
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


@app.route('/enterprise/suggestion', methods=['POST'])
def make_enterprise_suggestion():
    """
        make_enterprise_suggestion(): a enterprise can create a suggestion and we can read through them.
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
            return(jsonify("We would love your suggestion but you need to create an account first"), 404)
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/enterprise/product=<id>/question', methods = ['POST', 'GET'])
def ask_ai_question(id):
    """
         ask_question(id): Companies can ask questions about a product using GPT-3 on their specific product and get review sample data.
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        data = request.json['data']
        question = data['question']
        date = datetime.timestamp(now)
        if claims['Enterprise'] is True:
            todo = GPT3QA.document(id)
            todo_dict = todo.get().to_dict()
            if todo_dict['company_id'] == uid:
                response = openai.Answer.create(
                    n=3,
                    temperature=0.35,
                    search_model="ada",
                    model="curie",
                    question=str(question),
                    file=upload['id'],
                    examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
                    examples=[["What is human life expectancy in the United States?", "78 years."],
                            ["what is the population of Seattle?", "Seattle's population is 724,305"]],
                    max_tokens=40,
                    stop=["\n", "<|endoftext|>"],
                )
                document_list = response['selected_documents']
                df = pd.DataFrame(data=document_list)
                text_list = df.nlargest(3, 'score')['text'].tolist()

                answer_response = str(response['answers'])
                todo.collection('responses').document(date).set({
                    str(question): answer_response,
                    "reviews": text_list,
                    "response_id":date 
                }, merge=True)

                return (jsonify({"AI Answer":answer_response, "Reviews": text_list}), 200)
            else:
                return ("You are not authorized to view this page"), 403
        else:
            return ("You are not authorized to view this page"), 403
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route("/enterprise/product=<id>/ai", methods=['GET'])
def get_gpt3_data(id):
    """
         get_gpt3_data(id): Companies can see GPT-3 asked questions/answers and their review samples
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            todo = GPT3QA.document(id).get().to_dict()
            if todo['company_id'] == uid:
                query_ref = GPT3QA.document(id).collection('responses')
                documents = [doc.to_dict() for doc in query_ref.strem()]
                return (jsonify({"responses":documents}),200)
            else:
                return (jsonify("You are not authorized to view this page"), 403)
        else:
            return (jsonify("You are not authorized to view this page"), 403)
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
            return (jsonify("You are not authorized to view this page"), 403)
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
            return (jsonify("You are not authorized to view this specific enterprise analytics page."), 403)
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/demo', methods = ['GET'])
def get_demo_analytics():
    """
         get_demo_analytics(): this will be a demo product, to show on main site.
    """
    try:
        id = "1622679592.92769629oxyH0nhRZO141bNYz327SBxsJ3"
        todo = ADVANCED_ANALYTICS.document(id).get().to_dict()
        return jsonify(todo), 200
    except Exception as e:
        return f"An Error Occured: {e}"
        
@app.route('/demo/question', methods = ['POST', 'GET'])
def demo_ai_question():
    """
         ask_question(id): Companies can ask questions about a product using GPT-3 on their specific product.
    """
    now = datetime.now()
    try:
        data = request.json['data']
        question = data['question']
        response = openai.Answer.create(
            search_model="ada",
            model="curie",
            question=str(question),
            file="file-ua1GevFXqOgWY5iXfSmuVMwW",
            examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
            examples=[["What is human life expectancy in the United States?", "78 years."],
                        ["what is the population of Seattle?", "Seattle's population is 724,305"]],
            max_tokens=40,
            stop=["\n", "<|endoftext|>"],
        )
        answer_response = str(response['answers'])

        return (jsonify({"AI Answer":answer_response}), 200)

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
            Competitor_flag = data['Competitor_flag']
            Amazon_link = data['amazon_link']
            product_document = PRODUCT.document(Product_id)
            product_document.set({
                'Category' : Category,
                'Company_name': Company_name,
                'Company_id' : Company_id,
                'Product_entry_date': Date,
                'Product_id': Product_id,
                #this is the path on google firestore Storage for images
                'Product_images_path': "enterprise/"+str(Product_id)+"/",
                'Product_name': Product_name,
                'Amazon_link': Amazon_link,
                'processed': False,
                'assigned' : False,
                'competitor_product': Competitor_flag,
                'review_guru_analytics': False
            })
            return jsonify({"success": True}), 200
        else:
            return (jsonify("You are not authorized to view this page"), 404)
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

@app.route('/product/dealoftheday', methods=['GET'])
def get_amazon_deal_of_the_day():
    """
        get_amazon_deal_of_the_day(): get basic analytics of product of the day.
    """
    try:
        today_date = datetime.datetime.now().date()
        query_ref = PRODUCT.where(u'AmazonDealOfDay', u'==', today_date)
        return jsonify({"deal_of_day": query_ref.to_dict()}), 200
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/product=<id>', methods=['GET'])
def get_basic_analytics(id):
    """
        get_basic_analytics(id): get basic analytics of a certain product by their ID.
    """
    try:
        # todo = PRODUCT.document(id).get()
        todo2 = BASIC_ANALYTICS.document(id).get()
        return jsonify({"BASIC_ANALYTICS: ": todo2.to_dict()}), 200
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/categories/<cat>/product=<id>', methods=['GET'])
def get_basic_analytics_by_category(id):
    """
        get_basic_analytics_by_category(id): get basic analytics by category.
    """
    try:
        # todo = PRODUCT.document(id).get()
        todo2 = BASIC_ANALYTICS.document(id).get()
        return jsonify({"BASIC_ANALYTICS: ": todo2.to_dict()}), 200
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/categories/<cat>', methods=['GET'])
def get_products_by_category(cat):
    """
        get_product_by_category(cat) : get products by their category.
    """
    try:
        query_ref = PRODUCT.where(u'Category', u'==', cat)
        documents = [doc.to_dict() for doc in query_ref.stream()]
        return (jsonify({"category_documents":documents}),200)
    except Exception as e:
        return f"An error Occured: {e}"

