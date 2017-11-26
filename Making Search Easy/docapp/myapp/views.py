# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

import sys
from django.contrib.auth.hashers import check_password, make_password

from myapp.forms import LoginForm, SignUpForm, PostForm
from myapp.models import UserModel, SessionToken, PostModel
from docapp.settings import BASE_DIR
from django.shortcuts import render, redirect
import urllib
import sendgrid
import os
import requests
from sendgrid.helpers.mail import *
from django.utils import timezone
import csv
import itertools

buckets = []
predict=""
sg = sendgrid.SendGridAPIClient(apikey='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')

url = ('https://newsapi.org/v2/top-headlines?'
       'sources=bbc-news&'
       'apiKey=e01640ad85cb4254980ef01b3a60f14d')

res = requests.get(url).json()
from_email = Email("abhishek.sharma.168.as@gmail.com")


def generate_itemsets(itemsets, buckets, pass_):
    if pass_ == 1:
        list_ = []
    for bucket in buckets:
        list_ = list_ + bucket
        items = set(list_)
        get_support(items, buckets, pass_)
    else:
        items = []
        for i in itemsets:
            if type(i) is list:
                for itr in i:
                    if itr not in items:
                        items.append(itr)
            else:
                items.append(i)

    cmb = itertools.combinations(items, pass_)
    list_ = [list(elem) for elem in cmb]

    get_support(list_, buckets, pass_)


def get_support(items, buckets, pass_):
    dict_main = {}
    ctr = 0
    for i in items:
        dict_main[ctr] = i
        ctr = ctr + 1

    dict_ = {}
    for key, values in dict_main.iteritems():
        dict_[key] = 0
        for bucket in buckets:
            if type(values) is list:
                if all(val in bucket for val in values):
                    dict_[key] = int(dict_[key]) + 1
            else:
                if values in bucket:
                    dict_[key] = int(dict_[key]) + 1

    frequent_itemset = frequent_itemsets(dict_, pass_)

    frequent = []
    for f in frequent_itemset:
        frequent.append(dict_main[f])

    if frequent_itemset:
        pass_ = pass_ + 1
        generate_itemsets(frequent, buckets, pass_)


def frequent_itemsets(dict_, pass_):
    frequent = []
    for key, value in dict_.iteritems():
        if value > 8:
            frequent.append(key)
    return frequent


def calculate_confidence(X, Y, buckets):
    occr_X = 0
    occr_Y = 0
    for bucket in buckets:
        if type(X) is list:
            if all(val in bucket for val in X):
                occr_X = int(occr_X) + 1
        else:
            if X in bucket:
                occr_X = int(occr_X) + 1
        if type(Y) is list:
            if all(val in bucket for val in Y):
                occr_Y = int(occr_Y) + 1
        else:
            if Y in bucket:
                occr_Y = int(occr_Y) + 1

    conf = float(occr_Y) / float(occr_X) * 100
    return conf


def get_disease(symptomlist, buckets):
    disease_score = {}
    score = 0
    prediction = []
    for bucket in buckets:
        score = set(symptomlist) & set(bucket)
        score = float(len(score)) / float(len(symptomlist)) * 100
        if score > 0:
            disease = get_disease_given_bucket(bucket)
            disease_score[disease] = score
    for key, value in disease_score.items():
        if key != '' and value != '':
            prediction.append([key, value])
    return prediction


def get_disease_given_bucket(bucket):
    disease = ""
    with open(BASE_DIR + "/myapp/static/bucketmap.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            row_clean = [i for i in row if i]
            bucket_clean = [i for i in bucket if i]
            if len(row_clean) == (len(bucket_clean) + 1):
                if all(values in row_clean for values in bucket_clean):
                    disease = row_clean[0]
                    break
    return disease


def contact_view(request):
    return render(request, 'contact.html')

def main_view(request):
    return render(request, 'main.html')

def post_view(request):
    print("out")
    print(request.method)
    print("inn")
    print("inninn")
    global res
    PostModel.objects.all().delete()
    for i in range(len(res["articles"])):
        image = res["articles"][i]["urlToImage"]
        heading = res['articles'][i]["title"]
        definition = res['articles'][i]["description"]
        news_url = res['articles'][i]["url"]
        post = PostModel(image=image, heading=heading, definition=definition,news_url=news_url)
        post.save()
    posts = PostModel.objects.all()
    print(posts)
    return render(request, 'feed.html', {'posts': posts,'predict':predict})


def symptoms_view(request):
    global predict
    if request.method == 'POST':
            sym1 = request.POST.get('sym1')
            sym2 = request.POST.get('sym2')
            sym3 = request.POST.get('sym3')
            sym4 = request.POST.get('sym4')
            print(sym1)
            print(sym2)
            print(sym3)
            print(sym4)
            with open(BASE_DIR + "/myapp/static/buckets.csv") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    buckets.append(row)
            pass_ = 1
            itemsets = []
            symptomlist = [sym1,sym2,sym3,sym4]
            while '' in symptomlist:
                symptomlist.remove('')
            print(symptomlist)
            result = get_disease(symptomlist, buckets)
            print(result)
            chances = []
            max_chances = max([i[1] for i in result])
            print('max', max_chances)
            for i in result:
                if i[1] == max_chances:
                    chances.append(i[0])
            predict = ', '.join(chances)
            print(predict)
            return redirect('/feed/')

    else:
        return redirect('/login/')


