from django.shortcuts import render,redirect,HttpResponse,HttpResponseRedirect
from coverapp.models import Cover,Cart,Address,Order
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.db.models import Q #
from datetime import date,timedelta,datetime
import uuid
import random
import razorpay
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
def AddCover(request):
    n="Iphone15"
    d="latest covers"
    p="500"
    cart=Cover.objects.create(name=n,description=d,price=p)
    cart.save()
    return HttpResponse("Cover Added !!")

def AboutUs(request):
    return render(request,'aboutus.html')

def MyOrders(request):
    return render(request,'orders.html')


def home(request):
    context={}
    data = Cover.objects.all()
    context['covers']=data
    return render(request,'index.html',context)

def showCoverDetails(request,rid):
   context={}
   data = Cover.objects.get(id=rid)
   context['cover']=data
   return render(request,'details.html',context)

def registerUser(request):
   if request.method =="GET":
      return render(request,'registration.html')
   else:      
      # 1. capture the values entered by user
      u = request.POST['username']
      if User.objects.filter(username=u).exists():
         context={'error':'Username already registered!! Please enter a different username for registration. '}
         return render(request,'registration.html',context)
      else:
         e = request.POST['email']
         p = request.POST['password']
         cp = request.POST['confirmpassword']
         # form validation
         if u=='' or e=='' or p=='' or cp=='':
            context={'error':'all fields are compulsory'}
            return render(request,'registration.html',context)
         elif p != cp :
            context={'error':'Password and Confirm Password must be same'}
            return render(request,'registration.html',context)
         else:
            #2.  insert in db
            # u = User.objects.create(username=u,password=p,email=e)
            # u.save()
            # above code will insert user details in table, but password is in plain text and not encrypted
            #use below code so as to encrypt the password, for security
            u = User.objects.create(username=u,email=e)
            u.set_password(p)# for password encryption
            u.save()  
            # context = {'success':'Registred successfully , plz login'} 
            messages.success(request,'Registered successfully, Please login')
            return redirect('/login')

def userLogin(request):
    if request.method == "GET":
        return render(request,'login.html')
    else:
        # Login Activity
        u = request.POST['username']
        p = request.POST['password']
        ur = authenticate(username=u, password=p)
        print(ur)
        if ur == None:
            context={'error':'Please provide correct details to login'}
            return render(request,'login.html',context)
        else:
            login(request,ur)
            return redirect("/")
        
def userLogout(request):
    logout(request)
    messages.success(request,'User Logged out successfully!')
    return redirect('/login/')

def addtocart(request,coverid):
    userid = request.user.id 
    if userid is None:
      context={'error':'Please login, so as to add your favourite Cover in your cart!!'}
      return render(request,'login.html',context)
    else:
      user = User.objects.get(id = userid)
      cover = Cover.objects.get(id=coverid) 
      cart = Cart.objects.create(uid=user, cid=cover)
      cart.save()
      messages.success(request,'Cover added to cart successfully !!')
      return redirect('/showcart/')     


def showmycart(request):
    user = request.user
    cart=Cart.objects.filter(uid = user.id)
    TotalBill=0
    for cover in cart:
        TotalBill += cover.cid.price * cover.quantity
    count = len(cart)
    context={}
    context['cart']=cart
    context['total']=TotalBill
    context['count']=count
    return render(request,'showcart.html',context)

def removeCart(request,cartid):
    cart= Cart.objects.filter(id=cartid)
    cart.delete()
    messages.success(request,'Cover removed successfully!!')
    return redirect('/showcart/')

def updateCart(request,opr,cartid):
    cart = Cart.objects.filter(id=cartid)
    if opr == '1':#opr is a string value [1]
        cart.update(quantity =cart[0].quantity + 1)
    else: 
        cart.update(quantity =cart[0].quantity - 1)
    messages.success(request,'Cover Updated successfully!!')
    return redirect('/showcart/')

def searchByrange(request):
    min = request.GET['min']
    max = request.GET['max']
    c1 = Q(price__gte = min)
    c2 = Q(price__lte = max)
    coverList = Cover.objects.filter(c1 & c2)
    context={'covers':coverList}
    return render(request,'index.html',context)

def sortByprice(request,dir):
    col=''
    if dir == 'asc':
       col = 'price'
    else:
       col = '-price'
    coverList = Cover.objects.all().order_by(col)
    context={'covers':coverList}
    return render(request,'index.html',context)

def search(request):
    query = request.GET.get('q')
    results = Cover.objects.filter(name__icontains=query)  # Search covers by name

    return render(request, 'search.html', {'results': results, 'query': query})

def Cart_Address(request):
    if request.user.is_authenticated:
        
        if request.method == 'POST':
            cname = request.POST.get('cname')
            flat = request.POST.get('flat')
            landmark = request.POST.get('landmark')
            city = request.POST.get('city')
            state = request.POST.get('state')
            pincode = request.POST.get('pincode')
            contact = request.POST.get('contact')
            acontact = request.POST.get('acontact')

            
            Address.objects.create(user=request.user,name=cname,flat=flat,landmark=landmark,city=city,state=state,pincode=pincode,contact=contact,contactA=acontact)
                
        data = Address.objects.filter(user_id=request.user)
        print(data)
        return render(request,'address.html',{'adata':data})
    else:
        return HttpResponseRedirect('/')
    
def Cart_Preorder(request,aid):
    if request.user.is_authenticated:
        cover_id = Cart.objects.filter(uid=request.user).values_list('cid',flat=True)
        print(cover_id)
        data = Cover.objects.filter(id__in=cover_id)
        print(data)
        adata = Address.objects.filter(id=aid)
        date1 = date.today()
        days = timedelta(days=7)
        delivery_date = date1+days
        return render(request,'cart_preorder.html',{'pdata':data,'adata':adata,'date':delivery_date,'aid':aid})
    else:   
        return HttpResponseRedirect('/')

@csrf_exempt
def Cart_OrderConfirm(request,aid):
    # if request.user.is_authenticated:
        try:
            cover_id = Cart.objects.filter(uid=request.user).values_list('cid',flat=True)
            address_id = aid
            date1 = datetime.now()
            datef = date1.strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4().hex)[:6]
            order_id = f'PS{datef}-{unique_id}'
            oid = request.user
            for i in list(cover_id):
                Order.objects.create(user_id=oid.id,cover_id=i,address_id=address_id,order_id=order_id)
                Cart.objects.filter(uid=request.user).delete()
            return render(request,'cart_orderconfirm.html')
        except:
            return render(request,'confirmation.html')
    # else:
    #     return HttpResponseRedirect('/')

# def confirm(request):




def Cart_Payment(request,aid):
    if request.user.is_authenticated:
        client = razorpay.Client(auth=("rzp_test_93atKPgF1eLJ4M", "ZighzyBxP2GddO81jA8fXqCy"))

        cid = Cart.objects.filter(uid=request.user).values_list('cid',flat=True)
        amount = Cover.objects.filter(id__in=cid).values_list('price',flat=True)
        
        amt=0

        for i in amount:
            amt+=i

        data = { "amount": amt, "currency": "INR", "receipt": "order_rcptid_11" }
        payment = client.order.create(data=data)

        context={}
        context['amt'] = data['amount']*100
        context['aid'] = aid

        return render(request,'cart_payment.html',context)
    else:
        return HttpResponseRedirect('/')
    
# def makepayment(request):
#     user=request.user
#     usercart= Cart.objects.filter(uid = user.id)
#     TotalBill=0
#     for c in usercart:
#         TotalBill += c.cid.price * c.quantity
    
#     client = razorpay.Client(auth=("rzp_test_lQqNbmnLrTPgQl", "gkGZfEytQawMibc6LSSXXwr7"))
#     data = { "amount": 500, "currency": "INR", "receipt": "" }
#     payment = client.order.create(data=data)
#     context={'data':payment}
#     return render(request,'payment.html',context)

def orders(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user_id=request.user.id)
        context = {'orders': orders}
        return render(request, 'orders.html', context)
    else:
        return HttpResponseRedirect('/')

def send_test_email(request):
    subject = 'Test Email from COVERHUB'
    message = 'Hello! This is a test email from COVERHUB.'
    recipient_list = ['recipient@example.com']  # Replace with the actual recipient email
    email_from = settings.EMAIL_HOST_USER

    try:
        send_mail(subject, message, email_from, recipient_list)
        return HttpResponse('Email sent successfully')
    except Exception as e:
        return HttpResponse(f'Failed to send email: {str(e)}')