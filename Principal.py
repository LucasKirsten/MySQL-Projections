# -*- coding: utf-8 -*-

import os

import pygtk
pygtk.require('2.0')
import gtk

import MySQLdb

import getpass as gt

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas.io import sql
from scipy import stats, integrate
from scipy.optimize import curve_fit

import seaborn as sns
sns.set(color_codes=True)

from sklearn.neighbors import KNeighborsClassifier
from sklearn.cross_validation import train_test_split
from sklearn import metrics

UI_FILE = 'Interface.ui'

class Tabela():
###Gerar Tabela###
    def gerar_tabela(self, widget=None, data=None, todos=False):
	ordemcre = self.builder.get_object('radio_crescente').get_active()
	ordemdec = self.builder.get_object('radio_decrescente').get_active()
	coluna_ordem = self.entrada_coluna.get_active_text()
	tabela,colunas=self.tabela,self.entrada_colunas.get_active_text()
	if todos==True:
	    colunas = '*'
	start_iter = self.buffer_filtro.get_start_iter()
        end_iter = self.buffer_filtro.get_end_iter()
        filtro = self.buffer_filtro.get_text(start_iter, end_iter, True)
        if filtro!='':
            if ordemdec==True:
                query = 'SELECT '+colunas+' FROM '+tabela+' WHERE '+filtro+' ORDER BY '+coluna_ordem+" DESC"
            elif ordemcre==True:
                query = "SELECT "+colunas+" FROM "+tabela+" WHERE "+filtro+' ORDER BY '+coluna_ordem
	    else:
		query = "SELECT "+colunas+" FROM "+tabela+" WHERE "+filtro
        else:
            if ordemdec==True:
                query = "SELECT "+colunas+" FROM "+tabela+' ORDER BY '+coluna_ordem+" DESC "    
            elif ordemcre==True:
                query = "SELECT "+colunas+" FROM "+tabela+' ORDER BY '+coluna_ordem
	    else:
		query = "SELECT "+colunas+" FROM "+tabela
	try: 
	    os.system('cls' if os.name == 'nt' else 'clear')
            tabela = sql.read_sql(query, self.mdb)
	    pd.set_option('display.max_rows', len(tabela))
	    print tabela
	    print "\nVALORES SIGNIFICATIVOS:"
	    print tabela.describe()
	    return tabela.fillna(tabela.mean()) #preenche os valores nulos com o valor médio
	except pd.io.sql.DatabaseError:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para Seleção de Dados!")
	    message.run()
	    message.destroy()

    ###Salvar Tabela###
    def salvar_tabela(self,widget,data=None):
        dialog = gtk.FileChooserDialog("Salvar como...",
                                     None,
                                     gtk.FILE_CHOOSER_ACTION_SAVE,
                                     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                      gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)
   
        filter = gtk.FileFilter()
        filter.set_name("Tabela")
        filter.add_mime_type("application/excel")
        filter.add_pattern("*.xls")
        dialog.add_filter(filter)
   
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
	    tabela = self.gerar_tabela()
	    nome=dialog.get_filename()+'.xls'
	    writer = pd.ExcelWriter(nome, engine='xlsxwriter')
	    tabela.to_excel(writer, 'Sheet1')
	    writer.save()
        dialog.destroy()
    ####
    ###Adiciona '&&' aos filtros###
    def adicionar_E(self, widget=None):
        self.buffer_filtro.insert_at_cursor('&&')
    ####

    ###Adicionar '||' aos filtros###
    def adicionar_Ou(self,widget=None):
        self.buffer_filtro.insert_at_cursor('||')
    ###

    ###Adicionar 'NOT' aos filtros###
    def adicionar_Not(self, widget=None):
        self.buffer_filtro.insert_at_cursor('NOT ')

    def filtro_numero(self, widget):
        valores = self.builder.get_object('entry1').get_text()
        coluna = self.filtro_numero.get_active_text()
        index = self.entrada_numero.get_active()
        if index==0:
            valores = valores.split('-')
            filtro = coluna+'>'+valores[0]+'&&'+coluna+'<'+valores[1]
        else:
            vetor = ['>','<','=','>=','<=','!=']
            filtro=coluna+vetor[index-1]+valores
        filtro = filtro + '\n'
        self.buffer_filtro.insert_at_cursor(filtro)

    def filtro_caracter(self, widget):
        entrada = self.builder.get_object('entry2')
        coluna = self.filtro_caracter.get_active_text()
        carac = entrada.get_text()
        index = self.entrada_caracter.get_active()
        vetor=['=',carac+'%','%'+carac,'%'+carac+'%']
        if index==4:
            carac = int(carac)
            filtro = coluna+' LIKE '+'\''+'_'*carac+'\''
        elif index==0:
            filtro = coluna+vetor[0]+'\''+carac+'\''
        else:
            filtro = coluna+' LIKE '+'\''+vetor[index]+'\''
        filtro = filtro + '\n'
        self.buffer_filtro.insert_at_cursor(filtro)

    def filtro_data(self, widget):
        entrada = self.builder.get_object('entry3')
        coluna = self.filtro_data.get_active_text()
        data =  entrada.get_text()
        index = self.entrada_data.get_active()
        if index==3:
            data = data.split('/')
            filtro = coluna+'>'+'\''+data[0]+'\''+'&&'+coluna+'<'+'\''+data[1]+'\''
        else:
            data='\''+data+'\''
            vetor = ['=','>','<']
            filtro = coluna+vetor[index]+data
        filtro = filtro + '\n'
        self.buffer_filtro.insert_at_cursor(filtro)

    def construir(self, widget, vetor):
        liststore = gtk.ListStore(str)
        widget.set_model(liststore)
        for valor in vetor:
            liststore.append([valor])
        widget.set_text_column(0)
        widget.set_active(0)

    def escolha_tabela(self, entry):
	self.banco = entry.get_text()
        statemant = 'USE '+ entry.get_text()
	try:
            self.cur.execute(statemant)
	except:
	    return -1;
        liststore = gtk.ListStore(str)
        self.entrada_tabela.set_model(liststore)
        statemant = 'SHOW TABLES'
        self.cur.execute(statemant)
        table = self.cur.fetchall()
        for i in range(0,len(table)):
            liststore.append([table[i][0]])
        self.entrada_tabela.set_text_column(0)
        self.entrada_tabela.child.connect('changed', self.escolha_coluna)
        self.entrada_tabela.set_active(0)

    def escolha_coluna(self, entry):
	self.tabela = entry.get_text()
        statemant = 'DESCRIBE '+ entry.get_text()
	try:
            self.cur.execute(statemant)
	except:
	    return -1;
        liststore = gtk.ListStore(str)
	numero = gtk.ListStore(str)
	caracter = gtk.ListStore(str)
	data = gtk.ListStore(str)
        self.entrada_coluna.set_model(liststore)
	#Colunas que ser?o usadas para tabela e gr?ficos#
	self.entrada_colunas=self.builder.get_object('entrada_colunas')
	self.entrada_colunas.set_model(liststore)
	self.filtro_numero.set_model(numero)
	self.filtro_caracter.set_model(caracter)
	self.filtro_data.set_model(data)
	###
        mostrar_colunas = self.cur.fetchall()
        for vetor in mostrar_colunas:
            liststore.append([vetor[0]])
	    if 'char' in vetor[1]:
		caracter.append([vetor[0]])
	    elif 'date' in vetor[1]:
		data.append([vetor[0]])
	    elif 'int' or 'float' in vetor[1]:
	        numero.append([vetor[0]])
        self.entrada_coluna.set_text_column(0)
        self.entrada_coluna.set_active(0)
        self.filtro_numero.set_text_column(0)
        self.filtro_numero.set_active(0)
        self.filtro_caracter.set_text_column(0)
        self.filtro_caracter.set_active(0)
        self.filtro_data.set_text_column(0)
        self.filtro_data.set_active(0)
	#Colunas para tabela e gr?fico#
	self.entrada_colunas.set_text_column(0)
	###
    ###Importar Filtro###
    def importar_filtro(self,widget,data=None):
        dialog = gtk.FileChooserDialog("Abrir...",
                                     None,
                                     gtk.FILE_CHOOSER_ACTION_OPEN,
                                     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                      gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)
   
        filter = gtk.FileFilter()
        filter.set_name("Textos")
        filter.add_mime_type("text/plain")
        filter.add_pattern("*.txt")
        dialog.add_filter(filter)
   
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            arquivo=open(dialog.get_filename(), 'r')
	    start_iter = self.buffer_filtro.get_start_iter()
            end_iter = self.buffer_filtro.get_end_iter()
	    self.buffer_filtro.delete(start_iter,end_iter)
	    self.buffer_filtro.insert_at_cursor(arquivo.read())
	    arquivo.close()
        dialog.destroy()
    ###

    ###Exportar Filtro###
    def exportar_filtro(self,widget,data=None):
        dialog = gtk.FileChooserDialog("Salvar como...",
                                     None,
                                     gtk.FILE_CHOOSER_ACTION_SAVE,
                                     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                      gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)
   
        filter = gtk.FileFilter()
        filter.set_name("Textos")
        filter.add_mime_type("text/plain")
        filter.add_pattern("*.txt")
        dialog.add_filter(filter)
   
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
	    nome=dialog.get_filename()+'.txt'
            arquivo=open(nome, 'w')
	    start_iter = self.buffer_filtro.get_start_iter()
            end_iter = self.buffer_filtro.get_end_iter()
            texto = self.buffer_filtro.get_text(start_iter, end_iter, True)
	    arquivo.write(texto)
	    arquivo.close()
        dialog.destroy()
    ###

class Regressoes():
	#LINEAR#
    def linear(self, widget=None, data=None):
	tabela = self.gerar_tabela()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
            x = np.array(tabela[eixoX])
	    y = np.array(tabela[eixoY])
	    plt.plot(x, y, 'ro',label="Valores")
	except ValueError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores fornecidos não são numéricos!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	def func(x, a, b, c):
	    return a*x+b
	try:
	    popt, pcov = curve_fit(func, x, y)
	    plt.plot(np.unique(x), func(np.unique(x), *popt), label="Curva gerada")
	    plt.legend(loc='upper left')
	    plt.title('{0}*x{1:+}'.format(popt[0],popt[1]))
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não é possível gerar essa Regressão!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###
	#QUADRATICA#
    def quadratica(self, widget=None, data=None):
	tabela = self.gerar_tabela()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
            x = np.array(tabela[eixoX])
	    y = np.array(tabela[eixoY])
	    plt.plot(x, y, 'ro',label="Valores")
	except ValueError:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores fornecidos não são numéricos!")
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	def func(x, a, b, c):
	    return a*x**2+b*x+c
	try:
	    popt, pcov = curve_fit(func, x, y)
	    plt.plot(np.unique(x), func(np.unique(x), *popt), label="Curva gerada")
	    plt.legend(loc='upper left')
	    plt.title('{0}*x^2{1:+}*x{2:+}'.format(*popt))
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não é possível gerar essa Regressão!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###
	#EXPONENCIAL#
    def exponencial(self, widget=None, data=None):
	tabela = self.gerar_tabela()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
            x = np.array(tabela[eixoX])
	    y = np.array(tabela[eixoY])
	    plt.plot(x, y, 'ro',label="Valores")
	except ValueError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores fornecidos não são numéricos!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	def func(x, a, b, c):
	    return a*np.exp(b*x)+c
	try:
	    popt, pcov = curve_fit(func, x, y)
	    plt.plot(np.unique(x), func(np.unique(x), *popt), label="Curva gerada")
	    plt.legend(loc='upper left')
	    plt.title('{0}*exp({1}*x){2:+}'.format(*popt))
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não é possível gerar essa Regressão!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###
	#LOG NATURAL#
    def logaritmo_natural(self, widget=None, data=None):
	tabela = self.gerar_tabela()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
            x = np.array(tabela[eixoX])
	    y = np.array(tabela[eixoY])
	    plt.plot(x, y, 'ro',label="Valores")
	except ValueError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores fornecidos não são numéricos!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	def func(x, a, b, c, d):
	    return a*np.log(b*x+c)+d
	try:
	    popt, pcov = curve_fit(func, x, y)
	    plt.plot(np.unique(x), func(np.unique(x), *popt), label="Curva gerada")
	    plt.legend(loc='upper left')
	    plt.title('{0}*log({1}*x{2:+}){3:+}'.format(*popt))
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
 	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não é possível gerar essa Regressão!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###
	#SENO#
    def seno(self, widget=None, data=None):
	tabela = self.gerar_tabela()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
            x = np.array(tabela[eixoX])
	    y = np.array(tabela[eixoY])
	    plt.plot(x, y, 'ro',label="Valores")
	except ValueError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores fornecidos não são numéricos!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	def func(x, a, b, c, d):
	    return a*np.sin(b*x+c)+d
	try:
	    popt, pcov = curve_fit(func, x, y)
	    plt.plot(np.unique(x), func(np.unique(x), *popt), label="Curva gerada")
	    plt.legend(loc='upper left')
	    plt.title('{0}*sin({1}*x{2:+}){3:+}'.format(*popt))
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não é possível gerar essa Regressão!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;	
	###
	#COSSENO#
    def cosseno(self, widget=None, data=None):
	tabela = self.gerar_tabela()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
            x = np.array(tabela[eixoX])
	    y = np.array(tabela[eixoY])
	    plt.plot(x, y, 'ro',label="Valores")
	except ValueError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores fornecidos não são numéricos!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	def func(x, a, b, c, d):
	    return a*np.cos(b*x+c)+d
	try:
	    popt, pcov = curve_fit(func, x, y)
	    plt.plot(np.unique(x), func(np.unique(x), *popt), label="Curva gerada")
	    plt.legend(loc='upper left')
    	    plt.title('{0}*cos({1}*x{2:+}){3:+}'.format(*popt))
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não é possível gerar essa Regressão!\n")
 	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###

class GraficoSimples():
	#LINHA
    def simples_linha(self, widget,data=None):  
        def verifica(valor):
            valor = valor if valor!="" else None
            return valor
        def separa(valor):
            valor = valor.split('-') if valor!=None else None
            return valor
        tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	logx=self.builder.get_object('check_logx').get_active()
	logy=self.builder.get_object('check_logy').get_active()
	separar=self.builder.get_object('check_separar').get_active()
	legenda=self.builder.get_object('check_legenda').get_active()
        titulo,eixoX,eixoY = verifica(titulo),verifica(eixoX),verifica(eixoY)
	
	try:
            p=tabela.plot(kind='line',title=titulo,x=eixoX,y=eixoY,subplots=separar,\
            legend=legenda,logx=logx,logy=logy)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
 	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;  

	#BARRA HORIZONTAL
    def simples_barra_horizontal(self, widget, data=None):
        def verifica(valor):
            valor = valor if valor!="" else None
            return valor
        def separa(valor):
            valor = valor.split('-') if valor!=None else None
            return valor
        tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	logx=self.builder.get_object('check_logx').get_active()
	logy=self.builder.get_object('check_logy').get_active()
	separar=self.builder.get_object('check_separar').get_active()
	legenda=self.builder.get_object('check_legenda').get_active()
        titulo,eixoX,eixoY = verifica(titulo),verifica(eixoX),verifica(eixoY)
	
	try:
            p=tabela.plot(kind='barh',title=titulo,x=eixoX,y=eixoY,subplots=separar,\
        legend=legenda,logx=logx,logy=logy)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
 	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;  

	#BARRA VERTICALS
    def simples_barra_vertical(self, widget, data=None):
        def verifica(valor):
            valor = valor if valor!="" else None
            return valor
        def separa(valor):
            valor = valor.split('-') if valor!=None else None
            return valor
        tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	logx=self.builder.get_object('check_logx').get_active()
	logy=self.builder.get_object('check_logy').get_active()
	separar=self.builder.get_object('check_separar').get_active()
	legenda=self.builder.get_object('check_legenda').get_active()
        titulo,eixoX,eixoY = verifica(titulo),verifica(eixoX),verifica(eixoY)

	try:
            p=tabela.plot(kind='bar',title=titulo,x=eixoX,y=eixoY,subplots=separar,\
        legend=legenda,logx=logx,logy=logy)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
 	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;  
	###

class GraficoAvancado():
	###DENSIDADE###
    def avanc_densidade(self, widget=None, data=None):
        tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	c,e=0,0
	for i in tabela:
    	    try:
	        c=c+1;
                sns.distplot(tabela[i], label=i)
    	    except:
	        e=e+1;
	if (c-e!=0):
            plt.legend()
	    plt.title(titulo)
	    plt.show()
	else:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não é possível calcular Densidade!\n")
	    message.run()
	    message.destroy()
	###
	###DISCRETO###
    def avanc_discreto(self, widget=None, data=None):
        tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
	    sns.jointplot(x=eixoX, y=eixoY, data=tabela)
	    plt.xlabel(eixoX)
	    plt.ylabel(eixoY)
	    plt.title(titulo)
	    plt.show()
	except IndexError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except TypeError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except ValueError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;  
	###
	###PROXIMIDADE###
    def avanc_proximidade(self, widget=None, data=None):
	tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
	    sns.jointplot(x=eixoX, y=eixoY, data=tabela, kind="kde")
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
	    plt.title(titulo)
	except IndexError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except TypeError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
 	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;  
	plt.show()
	###
	###PROXIMIDADE+DISCRETO###
    def avanc_prox_discreto(self, widget=None, data=None):
	tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	eixoX=self.builder.get_object('entrada_eixoX').get_text()
	eixoY=self.builder.get_object('entrada_eixoY').get_text()
	try:
	    g = sns.jointplot(x=eixoX, y=eixoY, data=tabela, kind="kde", color="m")
	    g.plot_joint(plt.scatter, c="w", s=30, linewidth=1, marker="+")
	    g.ax_joint.collections[0].set_alpha(0)
	    g.set_axis_labels("$X$", "$Y$")
	    plt.ylabel(eixoY)
	    plt.xlabel(eixoX)
	    plt.title(titulo)
	    plt.show()
	except IndexError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except TypeError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valores inválidos para eixos X e Y!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###
	###JUNCAO DISCRETO###
    def avanc_juncao_discreto(self,widget=None, data=None):
	tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	try:
	    sns.pairplot(data=tabela)
	    plt.title(titulo)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###
	###JUNCAO PROXIMIDADE###
    def avanc_juncao_proximidade(self,widget=None, data=None):
	tabela = self.gerar_tabela(None)
	titulo=self.builder.get_object('entrada_titulo').get_text()
	try:
	    g = sns.PairGrid(data=tabela)
	    g.map_diag(sns.kdeplot)
	    g.map_offdiag(sns.kdeplot, cmap="Blues_d", n_levels=6)
	    plt.title(titulo)
	    plt.show()
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar esse Gráfico!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	###

class AprendizadoKNN():
    def aprendizado_knn(self,widget=None, data=None):
	iteracoes_K = int(self.builder.get_object('spinbutton_KNN').get_value())
	colunas = self.entrada_colunas.get_active_text()
	colunas = colunas.split(',')
	coluna_teste=self.builder.get_object('entry_coluna_KNN').get_text()
	dados = self.builder.get_object('entry_dados_KNN').get_text()
	dados = dados.split(',')
	#Lógica para ajustar os valores X e Y que serão usados no método
	nomes,y = [],[]
	coluna_y = coluna_teste
	try:
	    tabela = self.gerar_tabela(todos=True)
	    for n in tabela[coluna_y]:
                if n not in nomes:
                    nomes.append(n)
	    y = [i for i in range(0,len(nomes))]
	    colunas_x = colunas
	    dic = {}
	    for i in range(0, len(y)):
                dic[nomes[i]]=y[i]
	    y=[]
	    for n in tabela[coluna_y]:
                y.append(dic[n])
	    X,aux=[],[]
	    for i in range(0, len(tabela)):
                aux=[]
                for valor in colunas_x:
                    aux.append(tabela[valor][i])
                X.append(aux)
	    #Treina e testa os valores para x e y
	    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=4)
	    # Verifica o melhor valor para K (n_neighbors)
	    precisao=-1
	    for K in range(1,iteracoes_K):
                knn = KNeighborsClassifier(n_neighbors=K)
                knn.fit(X_train, y_train)
                y_pred = knn.predict(X_test)
                nova_precisao = metrics.accuracy_score(y_test, y_pred)
                if nova_precisao>precisao:
                    precisao = nova_precisao
                    valor_K = K
	    #Valida o método com o melhor valor para K
	    knn = KNeighborsClassifier(n_neighbors=valor_K)
	    knn.fit(X_train, y_train)
	    y_pred = knn.predict(X_test)
	    #Informa o erro
	    print '\nPREVISAO COM KNN:'
	    print 'Erro: {0}%'.format((1-precisao)*100)
	    print 'Valor usado para K: {0}'.format(valor_K)
	    previsao = knn.predict(dados) #faz uma previsão com base nos dados
	    #Informa o nome da previsão com base no dicionário que foi criado
	    for nome in dic:
                if dic[nome]==previsao:
                    print 'Dados provaveis do grupo: {0}'.format(nome)
	###
	except KeyError as er:
	    print type(er)
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Colunas inválidas para previsão!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except UnboundLocalError:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valor de loops para K e/ou Dados de Agrupamento inválido!")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except ValueError as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Valor de loops para K e/ou Dados de Agrupamento inválido!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;
	except Exception as er:
	    message = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	    message.set_markup("Não foi possível gerar previsão KNN!\n")
	    message.format_secondary_text("Info: "+str(er))
	    message.run()
	    message.destroy()
	    return -1;

class Inicial(Tabela,GraficoSimples,GraficoAvancado,Regressoes,AprendizadoKNN):
    def __init__(self):
	os.system('cls' if os.name == 'nt' else 'clear')
	while(True):
	    usuario = raw_input('Usuario: ')
	    senha = gt.getpass(prompt='Senha: ', stream=None)
	    try:
                self.mdb=MySQLdb.connect('127.0.0.1',usuario,senha)
                self.cur=self.mdb.cursor()
	        break
	    except:
		raw_input('Usuario ou senha incorreto, tente novamente!')
		os.system('cls' if os.name == 'nt' else 'clear')
		continue

	self.tipo='line'
        
	###Construtor###
        self.builder=gtk.Builder()
        self.builder.add_from_file(UI_FILE)
        self.builder.connect_signals(self)

	###Janelas Usadas###
		#Janela Principal
        self.janela=self.builder.get_object('main_window')
        self.janela.set_position(gtk.WIN_POS_CENTER)
        self.janela.connect('destroy', lambda w: gtk.main_quit())
	###

        ###Botoes###
        def adicionar_botoes(botoes):
            for but in botoes:
                btn = self.builder.get_object(but)
                style = btn.get_style().copy()
                btn.set_style(style)
        adicionar_botoes(['importar_filtro', 'exportar_filtro', 'button_E', 'button_Ou', 'button_Not', 'gerar_filtro1', 'gerar_filtro2', 'gerar_filtro3'])
    	###

	###Texto dos Filtros###
	self.texto_filtro = self.builder.get_object('texto_filtro')
        self.buffer_filtro = self.texto_filtro.get_buffer()
        ###

	###Listas para Banco, Tabela e Coluna selecionados ###
        self.entrada_banco = self.builder.get_object('entrada_banco')
        self.entrada_tabela = self.builder.get_object('entrada_tabela')
        self.filtro_numero = self.builder.get_object('filtro_numero')
	self.filtro_caracter = self.builder.get_object('filtro_caracter')
	self.filtro_data = self.builder.get_object('filtro_data')
	self.entrada_coluna = self.builder.get_object('entrada_coluna')
        liststore = gtk.ListStore(str)
        self.entrada_banco.set_model(liststore)
        statemant = 'SHOW DATABASES'
        self.cur.execute(statemant)
        database = self.cur.fetchall()
        for i in range(0,len(database)):
            liststore.append([database[i][0]])
        self.entrada_banco.set_text_column(0)
        self.entrada_banco.child.connect('changed', self.escolha_tabela)
        self.entrada_banco.set_active(0)
	###

	###Lista dos valores para filtro de numero, caracter e data###
        self.entrada_numero = self.builder.get_object('entradas_numero')
        self.entrada_caracter = self.builder.get_object('entradas_caracter')
        self.entrada_data = self.builder.get_object('entradas_data')
        caracter = ['Igual a','Comeca com','Termina com','Contem','Possui \'x\' caracteres']
        numero = ['Entre','Maior que','Menor que','Igual a','Maior ou igual a','Menor ou igual a','Diferente de']
        data = ['Igual a','Depois de','Antes de','Entre']
        dados = [[self.entrada_numero,numero],[self.entrada_caracter,caracter],[self.entrada_data,data]]
        for var, vetor in dados:
            self.construir(var,vetor)
	###

	###Botoes para gerar filtros####
        self.numero_Ok = self.builder.get_object('numero_Ok')
        self.caracter_Ok = self.builder.get_object('caracter_Ok')
        self.data_Ok = self.builder.get_object('data_Ok')
	###

	##MOSTRAR TUDO###
        self.janela.show_all()
	####
	
	##LIMPA O TERMINAL###
	os.system('cls' if os.name == 'nt' else 'clear')
	###

    ###LIMPAR TERMINAL###
    def limpar_terminal(self, widget=None, data=None):
	os.system('cls' if os.name == 'nt' else 'clear')
    ###

    ###SOBRE###
    def ajuda_sobre(self, widget=None, data=None):
	about = gtk.AboutDialog()
	about.set_program_name("Projeções MySQL")
        about.set_version("0.1")
        about.set_authors(["Márcio Silva\tmarciojsmb@gmail.com","Lucas Kirsten\tlucasnkir@gmail.com"])
	about.set_copyright("Agradecimentos à Fundação CAPES e ao orientador Dr. Carlos Eduardo Pereira")
        about.set_comments("Análise estatística de bancos de dados")
        about.set_website("http://www.ufrgs.br/ufrgs/inicial")
        about.set_logo(gtk.gdk.pixbuf_new_from_file("logo.png"))
        about.run()
        about.destroy()

if __name__ == '__main__':
    Inicial()
    gtk.main()