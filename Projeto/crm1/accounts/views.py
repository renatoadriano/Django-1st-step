from sqlite3 import Date
from telnetlib import STATUS
from django.shortcuts import render, redirect 
from django.http import HttpResponse, JsonResponse
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

# Create your views here.
from .models import *
from .forms import OrderForm, CreateUserForm, CustomerForm
from .filters import OrderFilter, Order, DateFilter
from .decorators import unauthenticated_user, allowed_users, admin_only
from datetime import date, timedelta
import datetime
import numpy as np
import json

@unauthenticated_user
def registerPage(request):

	form = CreateUserForm()
	if request.method == 'POST':
		form = CreateUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			username = form.cleaned_data.get('username')

			group = Group.objects.get(name='customer')
			user.groups.add(group)
			#Added username after video because of error returning customer name if not added
			Customer.objects.create(
				user=user,
				name=user.username,
				)

			messages.success(request, 'Account was created for ' + username)

			return redirect('login')
		

	context = {'form':form}
	return render(request, 'accounts/register.html', context)

@unauthenticated_user
def loginPage(request):

	if request.method == 'POST':
		username = request.POST.get('username')
		password =request.POST.get('password')

		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			return redirect('home')
		else:
			messages.info(request, 'Username OR password is incorrect')

	context = {}
	return render(request, 'accounts/login.html', context)

def logoutUser(request):
	logout(request)
	return redirect('login')

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer', 'admin'])
def home(request):
	
	today_min = date.today()
	print (today_min.day)
	
	today_orders = Order.objects.filter(date_created__day = today_min.day)
	
	
	print(today_orders)
	orders = Order.objects.all()
	customers = Customer.objects.all()

	total_customers = customers.count()

	total_orders = orders.count()
	delivered = orders.filter(status='Delivered').count()
	pending = orders.filter(status='Pending').count()

	context = {'orders':orders, 'customers':customers,
	'total_orders':total_orders,'delivered':delivered,
	'pending':pending, 'today_orders':today_orders}

	return render(request, 'accounts/dashboard.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def userPage(request):
	orders = request.user.customer.order_set.all()

	total_orders = orders.count()
	delivered = orders.filter(status='Delivered').count()
	pending = orders.filter(status='Pending').count()

	print('ORDERS:', orders)

	context = {'orders':orders, 'total_orders':total_orders,
	'delivered':delivered,'pending':pending}
	return render(request, 'accounts/user.html', context)




@login_required(login_url='login')
@allowed_users(allowed_roles=['admin','customer'])
def add_products(request):
	
	if request.method == 'POST':
		#name = request.POST['name']
		#category = request.POST['category']
		#price = request.POST['price']

		prod_name = request.POST.get('prod_name')
		prod_price =request.POST.get('prod_price')
		prod_cat = request.POST.get('prod_cat')
		username= request.POST.get('username')

		print(prod_name, prod_price, prod_cat)
		products = Product(name = prod_name, price = prod_price, category = prod_cat, user= username)
		products.save()
		return JsonResponse({'status': 'true', 'message': 'Produto criado!'}, status=200, safe=False)
		
	else:
		pass

	products = Product.objects.all()
	context = {
		'name':prod_name, 'category':prod_cat, 'price':prod_price
	}

	return render(request, 'accounts/products.html', {'products':products})

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin','customer'])
def delete_products(request):
	prod_id = request.POST.get('prod_id')
	product = Product.objects.get(id = prod_id)
	print(product.name, product.category, product.price)

	if request.method == "POST":
		product.delete()
		return redirect('/')

	context = {'item':product}
	return render(request, 'accounts/products.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['customer', 'admin'])
def products(request):
	user = request.user
	print(user)
	products = Product.objects.all()
	
	context = {'products':products, 'username':user}
	return render(request, 'accounts/products.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def customer(request, pk_test):
	customer = Customer.objects.get(id=pk_test)

	orders = customer.order_set.all()
	order_count = orders.count()

	myFilter = OrderFilter(request.GET, queryset=orders)
	orders = myFilter.qs 

	context = {'customer':customer, 'orders':orders, 'order_count':order_count,
	'myFilter':myFilter}
	return render(request, 'accounts/customer.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def createOrder(request, pk):
	OrderFormSet = inlineformset_factory(Customer, Order, fields=('product', 'status'), extra=10 )
	customer = Customer.objects.get(id=pk)
	formset = OrderFormSet(queryset=Order.objects.none(),instance=customer)
	#form = OrderForm(initial={'customer':customer})
	if request.method == 'POST':
		#print('Printing POST:', request.POST)
		form = OrderForm(request.POST)
		formset = OrderFormSet(request.POST, instance=customer)
		if formset.is_valid():
			formset.save()
			return redirect('/')

	context = {'form':formset}
	return render(request, 'accounts/order_form.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def updateOrder(request, pk):
	order = Order.objects.get(id=pk)
	form = OrderForm(instance=order)
	print('ORDER:', order)
	if request.method == 'POST':

		form = OrderForm(request.POST, instance=order)
		if form.is_valid():
			form.save()
			return redirect('/')

	context = {'form':form}
	return render(request, 'accounts/order_form.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def deleteOrder(request, pk):
	order = Order.objects.get(id=pk)
	if request.method == "POST":
		order.delete()
		return redirect('/')

	context = {'item':order}
	return render(request, 'accounts/delete.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer', 'admin'])
def accountSettings(request):
	customer = request.user.customer
	form = CustomerForm(instance=customer)

	if request.method == 'POST':
		form = CustomerForm(request.POST, request.FILES,instance=customer)
		
		if form.is_valid():
			form.save()


	context = {'form':form}
	return render(request, 'accounts/account_settings.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer', 'admin'])
def graphics(request):
	orders = Order.objects.all()
	
 
	
	
	dates = ""
	order_date = np.array = []
	
	for i in orders:
		dates = i.date_created.strftime('%Y-%m-%d')
		order_date.append(dates)
		
	order_date = np.unique(order_date, axis=0)
	#conversão para array
	x = order_date.tolist()
	
	
	contagem = ""
	order_orders = []
	
	for i in order_date:		
		contagem = Order.objects.filter(date_created__date=i).count()		
		order_orders.append(contagem)

	

	array1 = json.dumps(x)
	array2 = json.dumps(order_orders)
	
	#criação de variável para o ZIP
	mylist = zip(x, order_orders) 
	#junção das arrays em zip
		
	

	for (a, b) in  zip(x, order_orders):
		print (a, b) # print das arrays em ordem e em correspondência
	

	context = {'orders':orders, 'array1':array1, 'array2':array2, 'x': x, 'mylist':mylist}
	return render(request, 'accounts/graphics.html', context)



@login_required(login_url='login')
@allowed_users(allowed_roles=['customer', 'admin'])
def searchorders(request):
	order = Order.objects.all()
	dates = ""
	order_date = np.array = []
	
	for i in order:
		dates = i.date_created.strftime('%Y-%m-%d')
		order_date.append(dates)
		
	order_date = np.unique(order_date, axis=0)
	#conversão para array
	x = order_date.tolist()
	
	
	contagem = ""
	order_orders = []
	
	for i in order_date:		
		contagem = Order.objects.filter(date_created__date=i).count()		
		order_orders.append(contagem)

	

	array1 = json.dumps(x)
	array2 = json.dumps(order_orders)
	
	#criação de variável para o ZIP
	mylist = zip(x, order_orders) 
	#junção das arrays em zip
		
	

	for (a, b) in  zip(x, order_orders):
		print (a, b) # print das arrays em ordem e em correspondência
	


	if request.method == "POST":
		
		orddate = request.POST.get('orddate')

		print(orddate)

		order = Order.objects.filter( date_created__date = orddate)
		

	else:
		pass
	
	
	context = {'order':order, 'array1':array1, 'array2':array2, 'x': x, 'mylist':mylist}
	return render(request, 'accounts/graphics.html', context)