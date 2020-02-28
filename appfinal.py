import boto3
import pickle
import numpy as np
from flask import Flask, request, jsonify, render_template, json

model = None
app = Flask(__name__)


########### My AWS credentials 
ACCESS_ID = 'AKIA******DVJ57A'
ACCESS_KEY = '1FrjwIIbYTgkwnC***********i1WAIchb'
ec2 = boto3.resource('ec2', region_name = 'us-east-2',aws_access_key_id=ACCESS_ID,aws_secret_access_key= ACCESS_KEY)

######## starting the ec2 instance
ec2.create_instances(ImageId = 'ami-08cec7c429219e339', MinCount = 1, MaxCount =1, InstanceType = 't2.micro')

######## bucket to store the prediction outputs
BUCKET_NAME = 'irismodel'

######## pickle file that runs logistic regression model to predict the species ( stored in the 'irismodel' bucket )
MODEL_FILE_NAME = 'iris_trained_model.pkl'

  


#### Function to laod the model  
def load_model():
    global model
    # model variable refers to the global variable
    with open('iris_trained_model.pkl', 'rb') as f:
        model = pickle.load(f)

@app.route('/')
def home():
    return render_template('index.html')

###### Function to predict the species
@app.route('/predict',methods=['POST'])
def predict():
    
    load_model()
    data = [int(x) for x in request.form.values()] # Get data posted as a json
    data = np.array(data)[np.newaxis, :]  # converts shape from (4,) to (1, 4)
    prediction = int(model.predict(data))  # runs globally loaded model on the data
    
    ### function to assign the species names to predicted outputs
    def species(i):
        switcher={
                0:'Setosa',
                1:'Versicolor',
                2:'Virginica',
                
             }
        return switcher.get(i,"Invalid entries")

    ######## storing the output to a s3 bucket
    json_pred = json.dumps(species(prediction))
    s3 = boto3.resource('s3',
         aws_access_key_id=ACCESS_ID,
         aws_secret_access_key= ACCESS_KEY)
    object = s3.Object('irismodel1', 'iris_predictions.txt')
    
    object.put(Body = json_pred)
    
    ####### stopping the ec2 instances when not running 
    
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        ec2.instances.filter(InstanceIds = instance.id).terminate() 
    return render_template('index.html', prediction_text='The Species is \'{}\''.format(species(prediction)))
    

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 8080)