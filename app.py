from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import Code.scrape_mars as sm
from Code.config import  mongo_uri
#mongo_url eg:-  mongodb+srv://<username>:<password>@clustermongo.fl9vl.mongodb.net/<dbname>?retryWrites=true&w=majority

#Configure Flask App
app = Flask(__name__)

#Configure flask_pymongo PyMongo
mongo = PyMongo(app, mongo_uri)

@app.route('/', defaults={'path':''})
@app.route('/<path:path>')
def catch_all(path):
    if path == '':
        # Find one record of data from the mongo database (Collection has only one record always!!)
        latest_data = mongo.db.mars_data.find_one()
        return render_template("index.html", latest = latest_data)
    elif path.lower() in ['scrape', 'scrape/']:
        #This route captures scrape path
        #scrape the data
        scraped_dict = sm.scrape()
        #Convert table to html
        scraped_dict['scrape_mars_facts_data'] = scraped_dict['scrape_mars_facts_data'].to_html(index=False, classes="mars-table table table-sm text-xsmall table-bordered table-hover table-condensed", header="true")
        #Update the mars_data collection with the scraped data
        mongo.db.mars_data.update_one({}, {'$set': scraped_dict}, upsert=True)
        return redirect('/', 302)
    else:
        return render_template("default.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
