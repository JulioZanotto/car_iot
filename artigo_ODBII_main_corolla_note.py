import kivy
kivy.require("1.10.0")
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock

#Leitura do arquivo CSV e treino da rede neural
import obd
import csv
import numpy as np
import pandas as pd
from joblib import dump,load
from sklearn.tree import DecisionTreeClassifier
import os
import wget
import time
import requests
import json
import pyowm

base_url="https://floating-shore-63323.herokuapp.com/api/dados"

#Tentativa de conexão para pegar arquivo joblib
try:
    file_url = 'https://floating-shore-63323.herokuapp.com/artigo.joblib'
    file_name = wget.download(file_url)
    
except:
    pass

classifier = load('artigo.joblib')

dici = {}
with open('distancia.json', 'r') as j:
    dici = json.load(j)

#Se nao temperatura
temperatura = {'temp':25}

connection = obd.OBD(portstr='COM4')
#Previsão dos valores
#Coleta dos valores

dici4 = {"4":"Calculated Engine Load",
        "5":"Engine Coolant Temperature",
        "6":"Short Term Fuel Trim - Bank 1",
        "7":"Long Term Fuel Trim - Bank 1",
        "8":"Short Term Fuel Trim - Bank 2",
        "9":"Long Term Fuel Trim - Bank 2",
        "10":"Fuel Pressure",
        "11":"Intake Manifold Pressure",
        "12":"Engine RPM",
        "13":"Vehicle Speed",
        "14":"Timing Advance",
        "15":"Intake Air Temp",
        "16":"Air Flow Rate (MAF)",
        "17":"Throttle Position",
        }

class CarNeural(GridLayout):
    temp1 = StringProperty()
    speed1 = StringProperty()
    rpm1 = StringProperty()
    neural_network = StringProperty()
    global classifier
    global connection

    def __init__(self, **kwargs):
        global classifier
        global connection
        global dici
        global temperatura
        global base_url
        global dici4
        super(CarNeural, self).__init__(**kwargs)
        Clock.schedule_interval(self.escrita,1)
        Clock.schedule_interval(self.updist,10)
        Clock.schedule_interval(self.gettemp,3600)
        self.speed1 = str(0)
        self.rpm1 = str(0)
        self.temp1 = str(0)
        self.dist = int(0)
        self.ambiente = int(0)
        self.tempatual = {}
        self.coleta = 0
        self.lbl.text = 'Inicio'
        try:
            owm = pyowm.OWM('930a80bbd0400d7db87a73ad9163a8c4')
            observation = owm.weather_at_place('Sorocaba,BR')
            self.w = observation.get_weather()
            self.tempatual = self.w.get_temperature('celsius')
            self.flag = True

        except Exception:
            self.tempatual = temperatura
            self.temp_flag = False

        self.manutencao = dici['distancia']
        self.status = 0

        
    def escrita(self,dt):
        
        response = connection.query(obd.commands[1][5])
        self.coleta = response.value.magnitude

        distancia = self.dist

        self.ambiente = self.tempatual['temp']
        valor = np.array([[self.coleta,self.ambiente,distancia]])


        y_pred = classifier.predict(valor)#valor a prever

        convers2 = {'[0]':'Ok','[1]':'Attention','[2]':'Danger'}
        result_final = convers2[str(y_pred)]

        if y_pred == [0]:
                self.lbl.text = str(result_final)
                self.lbl.color = [0.9, 0.9, 0.9, 1]
                self.lbl.font_size = '20sp'

        elif y_pred == [1]:
                self.lbl.text = str(result_final)
                self.lbl.color = [0.9, 0.9, 0.0, 1]
                self.lbl.font_size = '20sp'

        else:
                self.lbl.text = str(result_final)
                self.lbl.color = [0.9, 0.0, 0.0, 1]
                self.lbl.font_size = '20sp'

        
        self.lbl6.text = str(self.ambiente)+" deg"
        self.lbl6.font_size = '20sp'  
        self.temp = connection.query(obd.commands[1][5])
        self.lbl2.text = str(self.temp)
        self.lbl2.font_size = '20sp'
        self.speed = connection.query(obd.commands[1][13]).value.magnitude
        self.lbl3.text = str(self.speed)+" Km/h"
        self.lbl3.font_size = '20sp'
        self.rpm = connection.query(obd.commands[1][12]).value.magnitude
        self.lbl4.text = str(self.rpm)+" RPM"
        self.lbl4.font_size = '20sp'
        self.lbl5.text = str(self.dist)+ " Km"
        self.lbl5.font_size = '20sp'

        self.manutencao += (self.speed/3.6)

        if self.status == 1:
        	self.manutencao = 0
        	dici['distancia'] = 0

        	with open('distancia.json', 'w') as j:
        		json.dump(dici, j)
        	self.status = 0

        else:
        	dici['distancia'] = self.manutencao

        	with open('distancia.json', 'w') as j:
        		json.dump(dici, j)

        if self.manutencao >= 10000000:
        	self.lbl7.text = "Change Oil!"
        	self.lbl7.color = [0.9, 0.0, 0.0, 1]
        else:
        	self.lbl7.text = str(round(self.manutencao/1000,2))+" Km"
        	self.lbl7.color = [0.9, 0.9, 0.9, 1]

 

    def btn_status(self):
        self.status = 1

    def updist(self,dt):
        self.dist = np.random.randint(8)
        dici3 = {}
        dici2 = {}

        for i in range(4,18):
            response = connection.query(obd.commands[1][i])
            if response.value == None:
                pass

            else:
                dici2[i]=response.value.magnitude
        '''
        for i in lista2:
            response = connection.query(obd.commands[1][i])
            coleta2.append(response.value.magnitude)
        '''
        '''
        dici2 = {
                  "info" : {
                            "Automovel": "Ford Fiesta",
                            "Motor": "1.6 Flex",
                            "Ano": "2010",
                            "Temperatura Ambiente": self.ambiente,
                            "Temperatura Motor": self.coleta,
                            "Calculated Engine Load": coleta2[0],
                            "Engine Coolant Temperature": coleta2[1],
                            "Short Term Fuel Trim - Bank 1": coleta2[2],
                            "Long Term Fuel Trim - Bank 1": coleta2[3],
                            "Timing Advance": coleta2[4],
                            "Intake Air Temp": coleta2[5],
                           }
                }
        '''

        for key,value in dici2.items():
            dici3[dici4.get(str(key))] = value

        dicionario = {"info Corolla":{}}
        dicionario["info Corolla"].update(dici3)

        data=json.dumps(dicionario)
        print(data)
        
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(base_url, data=data, headers = headers)


    def gettemp(self,dt):
        if self.temp_flag:
            self.tempatual = self.w.get_temperature('celsius')
        else:
            self.tempatual = temperatura

class Carroneural_fApp(App):
    def build(self):
        return CarNeural()



testeapp = Carroneural_fApp()
testeapp.run()
