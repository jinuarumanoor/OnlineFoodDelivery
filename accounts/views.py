
from django.http import HttpResponse
from django.shortcuts import render,redirect

from vendor.forms import VendorForm
from .forms import UserForm
from .models import User,UserProfile
from django.contrib import messages,auth
from .utils import detectUser,send_verification_email
from django.contrib.auth.decorators import login_required,user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from vendor.models import Vendor

# Restricting the vendor from the customer accessing page
def check_role_vendor(user):
    if user.role == 1:
        return True
    else:
        raise PermissionDenied



# Restricting the customer from accessing the vendor page
def check_role_customer(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied
def registerUser(request):
    if request.user.is_authenticated:
       messages.warning(request,'you are already logged in')
       return redirect('myAccount')
    elif request.method =='POST':
        print(request.POST)
        form=UserForm(request.POST)
        if form.is_valid():

            #create the user using the form
            # password=form.cleaned_data['password']
            # user=form.save(commit=False)
            # user.set_password(user.password)
            # user.role=user.CUSTOMER
            # user.save()

            #create the user using create user method
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            username=form.cleaned_data['username']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            user=User.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
            user.role=user.CUSTOMER
            user.save()
           #send verification email
            mail_subject = ' Please Activate your account'
            email_template = 'accounts/emails/account_verification_email.html'
            send_verification_email(request,user,mail_subject,email_template)
            messages.success(request,'User created successfully')
            
            form=UserForm()
        else:
            print('invalid form')
            print(form.errors)

    else:

        form=UserForm()
    context={
        'form':form,
    }
    return render(request, 'accounts/registerUser.html',context)


def registerVendor(request):
    if request.user.is_authenticated:
       messages.warning(request,'you are already logged in')
       return redirect('myAccount')
    if request.method=='POST':
        #STORE THE DATA AND CREATE THE USER
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST,request.FILES)
        if form.is_valid() and v_form.is_valid:
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            username=form.cleaned_data['username']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
            user.role = user.VENDOR
            user.save()
            vendor = v_form.save(commit=False)
            vendor.user = user    
            user_profile=UserProfile.objects.get(user=user)
            vendor.user_profile = user_profile
            vendor.save()

            #send verification email
            mail_subject = ' Please Activate your account'
            email_template = 'accounts/emails/account_verification_email.html'
            send_verification_email(request,user,mail_subject,email_template)

            messages.success(request,'your account has created succesfully!plaese wait for the approval from admin')
            return redirect('registerVendor')
        else:
            print('invalid form')
            print(form.errors)
    else:

        form=UserForm()
        v_form=VendorForm()

    context={
        'form':form,
        'v_form':v_form
    }
    return render(request,'accounts/registerVendor.html',context)

def activate(request,uidb64,token):
    #Activate the user by setting the user is_active to True
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(request,'congratulations!your account has been activated')
        return redirect('myAccount')
    else:
        messages.error(request,'invalid activation link')
        return redirect('myAccount')

        

    return
def login(request):
    if request.user.is_authenticated:
        messages.warning(request,'you are already logged in')
        return redirect('myAccount')
    elif request.method == 'POST':
        email=request.POST['email']
        password=request.POST['password']

        user=auth.authenticate(email=email,password=password)
        if user is not None:
            auth.login(request,user)
            messages.success(request,'logged in successfully')
            return redirect('myAccount')
        else:
            messages.error(request,'invalid credentials')   
            return redirect('login')
    return render(request,'accounts/login.html')   

def logout(request):
    auth.logout(request)
    messages.info(request,'logged out successfully')
    return redirect('login')

@login_required(login_url='login')
def myAccount(request):
    user=request.user
    redirectUrl= detectUser(user)
    return redirect(redirectUrl)
@login_required(login_url='login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    return render(request,'accounts/custDashboard.html')

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request,'accounts/vendorDashboard.html')

def forgot_password(request):
    if request.method == 'POST':
        email=request.POST['email']
        if User.objects.filter(email=email).exists():
            user=User.objects.get(email__exact=email)

            #send reset password Email
            mail_subject='Reset your password'
            email_template='accounts/emails/reset_password_email.html'
            send_verification_email(request,user,mail_subject,email_template)
            messages.success(request,'Password reset email has been sent to your email address')
            return redirect('login')
        else:
            messages.error(request,'Account does not exist')
            return redirect('forgot_password')
         
         
    return render(request,'accounts/forgot_password.html')

def reset_password_validate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user=None


    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] = uid
        messages.info(request,'Please reset your password')
        return redirect('reset_password')
    else:
        messages.error(request,'This link has been expired')
        return redirect('myAccount')
  


def reset_password(request):
    if request.method =='POST':
        print(request.POST)
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')

        if password == confirm_password:
            pk=request.session.get('uid')
            user=User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active=True
            user.save()
            messages.success(request,'Password reset successfully')
            return redirect('login')
        else:
            messages.error(request,'Password does not match')
            return redirect('reset_password')
        
    return render(request,'accounts/reset_password.html')
    